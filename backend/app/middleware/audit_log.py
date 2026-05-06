import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.db import async_session_maker
from app.core.security import decode_access_token
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# Endpoints to skip (docs, health, static assets)
_SKIP_PREFIXES = ("/api/v1/docs", "/api/v1/redoc", "/openapi", "/health", "/static")

# Sensitive field names — values are replaced with "***"
_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "new_password",
        "current_password",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "credit_card",
        "card_number",
        "cvv",
        "authorization",
        "setting_value",
    }
)

# Max body size stored in DB (10 KB)
_MAX_BODY_BYTES = 10_240


def _extract_module(path: str) -> str | None:
    api_prefix = f"{settings.API_V1_STR}/"
    if not path.startswith(api_prefix):
        return None
    module = path[len(api_prefix):].split("/", 1)[0].strip()
    return module or None


def _extract_operation(request: Request) -> str | None:
    route = request.scope.get("route")
    if not isinstance(route, APIRoute):
        return None
    return route.summary or None


def _sanitize(obj: object) -> object:
    """Recursively redact sensitive keys from a parsed JSON object."""
    if isinstance(obj, dict):
        return {
            k: "***" if k.lower() in _SENSITIVE_KEYS else _sanitize(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_sanitize(item) for item in obj]
    return obj


def _truncate(text: str, max_bytes: int = _MAX_BODY_BYTES) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore") + "…[truncated]"


def _sanitize_body(raw: bytes) -> str | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        sanitized = _sanitize(parsed)
        return _truncate(json.dumps(sanitized, ensure_ascii=False))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _truncate(raw.decode("utf-8", errors="replace"))


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Intercept every non-GET, non-skip request and record an AuditLog entry.

    Storage: always writes to DB. Optionally appends a JSON Lines file when
    settings.LOG_TO_FILE is True.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Skip read-only and infrastructure endpoints
        if request.method == "GET" or any(
            request.url.path.startswith(p) for p in _SKIP_PREFIXES
        ):
            return await call_next(request)

        start = time.monotonic()

        # Cache request body (Starlette streams it once)
        req_body = await request.body()

        # Extract user info from Authorization header (best-effort, no DB hit)
        user_id: uuid.UUID | None = None
        username: str | None = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_access_token(auth_header[7:])
            if payload and payload.get("sub"):
                try:
                    user_id = uuid.UUID(payload["sub"])
                except ValueError:
                    pass

        # Forward to actual handler
        response = await call_next(request)
        body_iterator = cast(Any, getattr(response, "body_iterator"))

        # Capture response body
        resp_chunks: list[bytes] = []
        async for chunk in body_iterator:
            resp_chunks.append(chunk)
        resp_body = b"".join(resp_chunks)

        duration_ms = int((time.monotonic() - start) * 1000)

        # Get client IP (respect X-Forwarded-For from reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        ip_address = (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else (request.client.host if request.client else None)
        )

        log_entry = AuditLog(
            user_id=user_id,
            username=username,
            http_method=request.method,
            endpoint=str(request.url.path),
            module=_extract_module(str(request.url.path)),
            operation=_extract_operation(request),
            request_body=_sanitize_body(req_body),
            response_body=_sanitize_body(resp_body),
            status_code=response.status_code,
            duration_ms=duration_ms,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
        )

        # Persist to DB (fire-and-forget; do not let DB errors break the response)
        try:
            async with async_session_maker() as session:
                session.add(log_entry)
                await session.commit()
        except Exception as exc:
            logger.warning("AuditLogMiddleware: DB write failed — %s", exc)

        # Optionally append to JSON Lines file
        if settings.LOG_TO_FILE:
            _append_file_log(log_entry)

        # Rebuild response (body was consumed above)
        return Response(
            content=resp_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


def _append_file_log(entry: AuditLog) -> None:
    try:
        log_path = Path(settings.LOG_FILE_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            {
                "id": str(entry.id),
                "user_id": str(entry.user_id) if entry.user_id else None,
                "method": entry.http_method,
                "endpoint": entry.endpoint,
                "status": entry.status_code,
                "duration_ms": entry.duration_ms,
                "ip": entry.ip_address,
                "ts": entry.created_at.isoformat(),
            },
            ensure_ascii=False,
        )
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as exc:
        logger.warning("AuditLogMiddleware: file write failed — %s", exc)
