import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.audit_log import AuditLog


async def create_audit_log(*, session: AsyncSession, log: AuditLog) -> None:
    session.add(log)
    await session.commit()


async def get_audit_logs(
    *,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    endpoint: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[AuditLog], int]:
    query = select(AuditLog)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if endpoint:
        query = query.where(AuditLog.endpoint.contains(endpoint))
    if start_time:
        query = query.where(AuditLog.created_at >= start_time)
    if end_time:
        query = query.where(AuditLog.created_at <= end_time)

    count_result = await session.execute(query)
    count = len(count_result.scalars().all())

    result = await session.execute(
        query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all()), count
