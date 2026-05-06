import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, permission_required
from app.crud import audit_logs as audit_logs_crud
from app.schemas.audit_log import AuditLogPublic, AuditLogsPublic

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get(
    "/",
    response_model=AuditLogsPublic,
    summary="查询操作日志",
    description="按模块、接口路径和时间范围查询操作日志。",
)
async def list_audit_logs(
    session: SessionDep,
    _: Annotated[None, Depends(permission_required("system.audit_logs.read"))],
    user_id: uuid.UUID | None = None,
    module: str | None = None,
    endpoint: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    skip: int = 0,
    limit: int = 50,
) -> AuditLogsPublic:
    """
    Query audit logs with optional filters.

    All params are optional. Results are sorted newest-first.
    """
    logs, count = await audit_logs_crud.get_audit_logs(
        session=session,
        user_id=user_id,
        module=module,
        endpoint=endpoint,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )
    return AuditLogsPublic(
        data=[AuditLogPublic.model_validate(log, from_attributes=True) for log in logs],
        count=count,
    )
