"""
Async HTTP client for WeChat Pay v3 API.

Builds the ``Authorization: WECHATPAY2-SHA256-RSA2048 …`` header, sends the
request via ``httpx``, and optionally verifies the response signature.
"""

from __future__ import annotations

import logging
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from cryptography.hazmat.primitives.asymmetric import rsa

from app.services.wechat_pay.crypto import (
    load_private_key,
    load_public_key,
    rsa_sign_sha256,
    rsa_verify_sha256,
)

logger = logging.getLogger(__name__)

WECHAT_PAY_BASE_URL = "https://api.mch.weixin.qq.com"


@dataclass
class WechatPayCredentials:
    """All credentials required to call WeChat Pay v3 APIs."""
    app_id: str
    mch_id: str
    api_v3_key: str
    cert_serial: str
    private_key_pem: str
    public_key_id: str
    public_key_pem: str
    notify_base_url: str = ""

    _private_key: rsa.RSAPrivateKey | None = field(default=None, repr=False)
    _public_key: rsa.RSAPublicKey | None = field(default=None, repr=False)

    @property
    def private_key(self) -> rsa.RSAPrivateKey:
        if self._private_key is None:
            self._private_key = load_private_key(self.private_key_pem)
        return self._private_key

    @property
    def public_key(self) -> rsa.RSAPublicKey:
        if self._public_key is None:
            self._public_key = load_public_key(self.public_key_pem)
        return self._public_key


async def load_credentials_from_settings() -> WechatPayCredentials:
    """Build :class:`WechatPayCredentials` from ``RuntimeSettingsService``."""
    from app.core.runtime_settings import runtime_settings

    app_id = await runtime_settings.get_str("wechat_pay_app_id")
    mch_id = await runtime_settings.get_str("wechat_pay_mch_id")
    api_v3_key = await runtime_settings.get_str("wechat_pay_api_v3_key")
    cert_serial = await runtime_settings.get_str("wechat_pay_cert_serial")
    private_key_pem = await runtime_settings.get_str("wechat_pay_private_key")
    public_key_id = await runtime_settings.get_str("wechat_pay_public_key_id")
    public_key_pem = await runtime_settings.get_str("wechat_pay_public_key")
    notify_base_url = await runtime_settings.get_str("wechat_pay_notify_base_url")

    return WechatPayCredentials(
        app_id=app_id,
        mch_id=mch_id,
        api_v3_key=api_v3_key,
        cert_serial=cert_serial,
        private_key_pem=private_key_pem,
        public_key_id=public_key_id,
        public_key_pem=public_key_pem,
        notify_base_url=notify_base_url.rstrip("/"),
    )


def _build_authorization(
    credentials: WechatPayCredentials,
    method: str,
    url_path: str,
    body: str,
) -> str:
    """Build the ``WECHATPAY2-SHA256-RSA2048`` Authorization header value.

    Signature message layout::

        HTTP_METHOD\\n
        URL_PATH\\n
        TIMESTAMP\\n
        NONCE\\n
        BODY\\n
    """
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    message = f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"
    signature = rsa_sign_sha256(credentials.private_key, message)
    return (
        f'WECHATPAY2-SHA256-RSA2048 '
        f'mchid="{credentials.mch_id}",'
        f'nonce_str="{nonce}",'
        f'signature="{signature}",'
        f'timestamp="{timestamp}",'
        f'serial_no="{credentials.cert_serial}"'
    )


def _verify_response_signature(
    credentials: WechatPayCredentials,
    headers: httpx.Headers,
    body: str,
) -> bool:
    """Verify the WeChat response signature using the platform public key."""
    timestamp = headers.get("Wechatpay-Timestamp", "")
    nonce = headers.get("Wechatpay-Nonce", "")
    signature = headers.get("Wechatpay-Signature", "")
    if not (timestamp and nonce and signature):
        return False
    message = f"{timestamp}\n{nonce}\n{body}\n"
    return rsa_verify_sha256(credentials.public_key, message, signature)


class WechatPayClient:
    """Thin async wrapper around ``httpx.AsyncClient`` with v3 signing."""

    def __init__(self, credentials: WechatPayCredentials) -> None:
        self.credentials = credentials

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        verify_response: bool = True,
    ) -> httpx.Response:
        """Send a signed request to the WeChat Pay API.

        Parameters
        ----------
        method:
            HTTP method (``GET``, ``POST``, …).
        path:
            URL path *without* the domain, e.g. ``/v3/pay/transactions/jsapi``.
        json_body:
            JSON-serialisable dict for the request body (``None`` for GET).
        verify_response:
            Whether to verify the response signature.  Disable for endpoints
            that return ``204 No Content`` (e.g. close order).
        """
        import json as _json

        body_str = _json.dumps(json_body, ensure_ascii=False) if json_body else ""
        authorization = _build_authorization(
            self.credentials, method.upper(), path, body_str,
        )
        headers = {
            "Authorization": authorization,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Wechatpay-Serial": self.credentials.public_key_id,
        }

        url = f"{WECHAT_PAY_BASE_URL}{path}"
        async with httpx.AsyncClient() as http:
            response = await http.request(
                method,
                url,
                content=body_str.encode() if body_str else None,
                headers=headers,
                timeout=30.0,
            )

        if verify_response and response.status_code in range(200, 300):
            if not _verify_response_signature(
                self.credentials, response.headers, response.text,
            ):
                logger.warning(
                    "WeChat Pay response signature verification failed for %s %s",
                    method,
                    path,
                )

        return response
