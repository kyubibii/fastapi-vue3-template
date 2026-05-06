import uuid
from datetime import datetime
from typing import Any, cast

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.audit_log import AuditLog
from app.models.user import User


async def _attach_usernames(
    *, session: AsyncSession, logs: list[AuditLog]
) -> list[AuditLog]:
    user_ids = list({log.user_id for log in logs if log.user_id is not None})
    if not user_ids:
        return logs

    result = await session.execute(
        select(User.id, User.username).where(cast(Any, User.id).in_(user_ids))
    )
    username_map = dict(result.all())

    for log in logs:
        if log.user_id is not None and log.user_id in username_map:
            log.username = username_map[log.user_id]

    return logs


async def create_audit_log(*, session: AsyncSession, log: AuditLog) -> None:
    session.add(log)
    await session.commit()


async def get_audit_logs(
    *,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    module: str | None = None,
    endpoint: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[AuditLog], int]:
    query = select(AuditLog)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if module:
        query = query.where(AuditLog.module == module)
    if endpoint:
        query = query.where(cast(Any, AuditLog.endpoint).contains(endpoint))
    if start_time:
        query = query.where(AuditLog.created_at >= start_time)
    if end_time:
        query = query.where(AuditLog.created_at <= end_time)

    count_result = await session.execute(
        select(func.count()).select_from(query.order_by(None).subquery())
    )
    count = int(count_result.scalar_one())

    result = await session.execute(
        query.order_by(cast(Any, AuditLog.created_at).desc()).offset(skip).limit(limit)
    )
    logs = list(result.scalars().all())
    logs = await _attach_usernames(session=session, logs=logs)
    return logs, count
