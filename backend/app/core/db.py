from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings


def _register_mysql_session_utc() -> None:
    uri = str(settings.SQLALCHEMY_DATABASE_URI)
    if not uri.startswith("mysql"):
        return

    @event.listens_for(engine.sync_engine, "connect")
    def _set_mysql_session_tz(dbapi_conn, connection_record) -> None:  # type: ignore[no-untyped-def]
        cur = dbapi_conn.cursor()
        cur.execute("SET SESSION time_zone = '+00:00'")
        cur.close()

_engine_kwargs: dict = {
    "pool_pre_ping": True,
    "echo": settings.ENVIRONMENT == "development",
}

# On Windows dev with auto-reload, pooled aiomysql connections can become stale
# across event-loop restarts and cause intermittent 500 errors.
if settings.ENVIRONMENT == "development":
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20

engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI), **_engine_kwargs)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

_register_mysql_session_utc()
