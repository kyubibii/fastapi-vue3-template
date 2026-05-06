"""
Job 注册表。

新增 Job：
1. 在 definitions/ 目录下创建对应的 async def run() 函数文件。
2. 在本文件 JOB_REGISTRY 列表中追加 JobDefinition 记录。

trigger 类型说明：
  - "cron"     — 类 cron 表达式，trigger_kwargs 支持 hour/minute/second/day_of_week 等
  - "interval" — 固定间隔，trigger_kwargs 支持 seconds/minutes/hours/days
  - "date"     — 一次性，trigger_kwargs 支持 run_date（datetime 对象或 ISO 字符串）
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from app.jobs.definitions import example_cron, example_date, example_interval


@dataclass
class JobDefinition:
    id: str
    name: str
    description: str
    func: Callable[[], Coroutine[Any, Any, None]]
    trigger: str
    trigger_kwargs: dict[str, Any] = field(default_factory=dict)
    default_enabled: bool = True


JOB_REGISTRY: list[JobDefinition] = [
    JobDefinition(
        id="example_cron",
        name="示例：Cron 日志清理",
        description="每天凌晨 02:00 执行，模拟定时日志清理任务。",
        func=example_cron.run,
        trigger="cron",
        trigger_kwargs={"hour": 2, "minute": 0},
        default_enabled=True,
    ),
    JobDefinition(
        id="example_interval",
        name="示例：Interval 健康检查",
        description="每 5 分钟执行一次，模拟服务健康检查心跳。",
        func=example_interval.run,
        trigger="interval",
        trigger_kwargs={"minutes": 5},
        default_enabled=True,
    ),
    JobDefinition(
        id="example_date",
        name="示例：Date 启动延迟任务",
        description="应用启动后 30 秒执行一次，适合初始化检查、数据预热。",
        func=example_date.run,
        trigger="date",
        # 使用 timedelta 作为特殊标记，setup_jobs() 会在注册时动态计算 run_date
        trigger_kwargs={"run_date": datetime.timedelta(seconds=30)},
        default_enabled=True,
    ),
]
