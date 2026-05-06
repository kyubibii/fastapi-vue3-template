"""
APScheduler AsyncIOScheduler 单例。

调用 setup_jobs() 将 JOB_REGISTRY 中 default_enabled=True 的任务注册到 scheduler。
在 FastAPI startup 时调用 setup_jobs() 后再 scheduler.start()，
在 shutdown 时调用 scheduler.shutdown(wait=False)。
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def setup_jobs() -> None:
    """将 JOB_REGISTRY 中已启用的任务注册到 scheduler。"""
    # 延迟导入，避免循环引用
    from app.jobs.registry import JOB_REGISTRY

    for job_def in JOB_REGISTRY:
        if not job_def.default_enabled:
            logger.info("Job '%s' is disabled, skipping.", job_def.id)
            continue

        # 对 date 触发器：若 run_date 是 timedelta，则基于当前时间动态计算
        import datetime
        trigger_kwargs = dict(job_def.trigger_kwargs)
        if job_def.trigger == "date" and isinstance(
            trigger_kwargs.get("run_date"), datetime.timedelta
        ):
            trigger_kwargs["run_date"] = (
                datetime.datetime.now() + trigger_kwargs["run_date"]
            )

        scheduler.add_job(
            job_def.func,
            trigger=job_def.trigger,
            id=job_def.id,
            name=job_def.name,
            replace_existing=True,
            **trigger_kwargs,
        )
        logger.info(
            "Registered job '%s' with trigger '%s'.",
            job_def.id,
            job_def.trigger,
        )
