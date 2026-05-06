"""
Job 调度管理 API 路由。

提供对 APScheduler 任务的查询、手动触发、暂停/恢复操作。
"""

import asyncio
import datetime
import logging
from typing import Annotated

from apscheduler.job import Job
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import permission_required
from app.jobs.registry import JOB_REGISTRY
from app.jobs.scheduler import scheduler
from app.schemas.job import JobPublic, JobsPublic, JobTriggerResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _trigger_description(job: Job) -> str:
    """将 APScheduler trigger 转换为人类可读字符串。"""
    trigger = job.trigger
    trigger_type = type(trigger).__name__

    if trigger_type == "CronTrigger":
        return str(trigger)
    elif trigger_type == "IntervalTrigger":
        return str(trigger)
    elif trigger_type == "DateTrigger":
        return str(trigger)
    return str(trigger)


def _build_job_public(job_id: str) -> JobPublic:
    """根据 job_id 构造 JobPublic，从 JOB_REGISTRY 取 description，从 scheduler 取运行状态。"""
    # 从注册表取描述信息
    reg_entry = next((j for j in JOB_REGISTRY if j.id == job_id), None)
    description = reg_entry.description if reg_entry else ""
    trigger_type_label = reg_entry.trigger if reg_entry else "unknown"

    # 从 scheduler 取运行状态
    job: Job | None = scheduler.get_job(job_id)

    if job is None:
        # Date 触发器的一次性任务执行完毕后会从 scheduler 中移除
        return JobPublic(
            id=job_id,
            name=reg_entry.name if reg_entry else job_id,
            description=description,
            trigger_type=trigger_type_label,
            trigger_description="已执行完毕（一次性任务）",
            next_run_time=None,
            is_paused=False,
        )

    return JobPublic(
        id=job.id,
        name=job.name,
        description=description,
        trigger_type=trigger_type_label,
        trigger_description=_trigger_description(job),
        next_run_time=job.next_run_time,
        is_paused=job.next_run_time is None,
    )


@router.get(
    "/",
    response_model=JobsPublic,
    summary="查询所有定时任务",
    description="返回 JOB_REGISTRY 中所有任务的名称、触发器配置及当前运行状态。",
)
async def list_jobs(
    _: Annotated[None, Depends(permission_required("system.jobs.read"))],
) -> JobsPublic:
    data = [_build_job_public(job_def.id) for job_def in JOB_REGISTRY]
    return JobsPublic(data=data)


@router.post(
    "/{job_id}/trigger",
    response_model=JobTriggerResult,
    summary="立即触发任务",
    description="立即执行指定任务一次，不影响原有调度计划。",
)
async def trigger_job(
    job_id: str,
    _: Annotated[None, Depends(permission_required("system.jobs.trigger"))],
) -> JobTriggerResult:
    reg_entry = next((j for j in JOB_REGISTRY if j.id == job_id), None)
    if not reg_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found in registry.",
        )

    logger.info("Manually triggering job '%s'.", job_id)
    asyncio.create_task(reg_entry.func())

    return JobTriggerResult(
        job_id=job_id,
        message=f"任务 '{reg_entry.name}' 已触发执行。",
        triggered_at=datetime.datetime.now(),
    )


@router.put(
    "/{job_id}/pause",
    response_model=JobPublic,
    summary="暂停任务",
    description="暂停指定任务，任务将不再按计划执行，直到恢复。",
)
async def pause_job(
    job_id: str,
    _: Annotated[None, Depends(permission_required("system.jobs.manage"))],
) -> JobPublic:
    job: Job | None = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found in scheduler (may have already completed).",
        )
    job.pause()
    logger.info("Job '%s' paused.", job_id)
    return _build_job_public(job_id)


@router.put(
    "/{job_id}/resume",
    response_model=JobPublic,
    summary="恢复任务",
    description="恢复已暂停的指定任务，任务将按原计划继续执行。",
)
async def resume_job(
    job_id: str,
    _: Annotated[None, Depends(permission_required("system.jobs.manage"))],
) -> JobPublic:
    job: Job | None = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found in scheduler (may have already completed).",
        )
    job.resume()
    logger.info("Job '%s' resumed.", job_id)
    return _build_job_public(job_id)
