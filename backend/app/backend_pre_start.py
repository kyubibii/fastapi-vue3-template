"""
Waits for the MySQL database to become available before the app starts.

Used in Dockerfile CMD:
    python app/backend_pre_start.py && alembic upgrade head && ...
"""

import asyncio
import logging

from sqlalchemy import text
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.db import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_TRIES = 60
WAIT_SECONDS = 1


@retry(
    stop=stop_after_attempt(MAX_TRIES),
    wait=wait_fixed(WAIT_SECONDS),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def check_db() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database is ready.")


def main() -> None:
    logger.info("Initializing service — waiting for database...")
    asyncio.run(check_db())


if __name__ == "__main__":
    main()
