import asyncio
import logging
from pathlib import Path

import sentry_sdk
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect
from sqlmodel import SQLModel
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.db import engine
from app.core.runtime_settings import bootstrap_settings_from_env
from app.initial_data import seed
from app.jobs.scheduler import scheduler, setup_jobs
from app.middleware.audit_log import AuditLogMiddleware
from app.models import *  # noqa: F401, F403

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"


def _build_alembic_config() -> Config:
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "app" / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))
    return alembic_cfg


def _run_migrations_sync() -> None:
    command.upgrade(_build_alembic_config(), "head")


def _stamp_head_sync() -> None:
    command.stamp(_build_alembic_config(), "head")


def _has_alembic_revisions() -> bool:
    return len(ScriptDirectory.from_config(_build_alembic_config()).get_heads()) > 0


async def _create_tables_from_metadata() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def _get_existing_table_names() -> set[str]:
    async with engine.connect() as conn:
        return await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))


async def _bootstrap_empty_database_and_stamp_head() -> bool:
    managed_tables = set(SQLModel.metadata.tables.keys())
    if not managed_tables:
        logger.warning("No SQLModel tables discovered; skipping metadata bootstrap.")
        return False

    existing_tables = await _get_existing_table_names()
    if existing_tables & managed_tables:
        return False

    logger.warning(
        "No managed tables found in target database; creating schema from metadata and stamping alembic head."
    )
    await _create_tables_from_metadata()
    await asyncio.to_thread(_stamp_head_sync)
    logger.info("Empty database bootstrap completed (metadata create_all + alembic stamp head).")
    return True


if settings.SENTRY_DSN and settings.ENVIRONMENT != "development":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    generate_unique_id_function=custom_generate_unique_id,
)


@app.on_event("startup")
async def startup_tasks() -> None:
    if settings.AUTO_MIGRATE_ON_STARTUP:
        if _has_alembic_revisions():
            bootstrapped = False
            if settings.AUTO_BOOTSTRAP_EMPTY_DB_WITH_METADATA:
                bootstrapped = await _bootstrap_empty_database_and_stamp_head()

            if not bootstrapped:
                logger.info("Running alembic migrations on startup...")
                # Alembic env uses asyncio.run; execute in thread to avoid active-loop conflict.
                await asyncio.to_thread(_run_migrations_sync)
                logger.info("Alembic migrations completed.")
        elif settings.AUTO_CREATE_TABLES_IF_NO_MIGRATIONS:
            logger.warning(
                "No alembic revision files found; creating tables from SQLModel metadata."
            )
            await _create_tables_from_metadata()
            logger.info("Tables created from SQLModel metadata.")
        else:
            logger.warning("No alembic revisions found; skipping database schema bootstrap.")

    if settings.AUTO_SEED_ON_STARTUP:
        logger.info("Seeding initial data on startup...")
        await seed()
        logger.info("Initial data seed completed.")

    inserted, skipped = await bootstrap_settings_from_env()
    if inserted or skipped:
        logger.info(
            "Settings bootstrap completed: inserted=%s skipped=%s",
            inserted,
            skipped,
        )

    setup_jobs()
    scheduler.start()
    logger.info("APScheduler started with %d jobs.", len(scheduler.get_jobs()))


@app.on_event("shutdown")
async def shutdown_tasks() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down.")
    await engine.dispose()

# ── CORS ───────────────────────────────────────────────────────────────────────
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ── Audit log middleware ───────────────────────────────────────────────────────
app.add_middleware(AuditLogMiddleware)

# ── API routes ─────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)

# ── Serve built frontend (single-port mode) ───────────────────────────────────
# Priority:
# 1) backend/app/static (container image output)
# 2) <project_root>/frontend/dist (local build output)
_backend_static = Path(__file__).parent / "static"
_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_static_dir = _backend_static if _backend_static.exists() else _frontend_dist
if _static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def frontend_app(full_path: str) -> FileResponse:
        requested_path = _static_dir / full_path
        if full_path and requested_path.is_file():
            return FileResponse(requested_path)
        return FileResponse(_static_dir / "index.html")
