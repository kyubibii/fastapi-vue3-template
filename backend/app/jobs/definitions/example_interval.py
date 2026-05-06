"""
示例：Interval 触发器任务

每 5 分钟执行一次，模拟健康检查心跳或数据同步。
"""

import logging

logger = logging.getLogger(__name__)


async def run() -> None:
    """每 5 分钟执行一次的示例任务（Interval 触发器）。"""
    logger.info("[example_interval] 健康检查心跳...")
    # TODO: 在此实现实际业务逻辑，例如检查外部服务可用性
    logger.info("[example_interval] 健康检查完成。")
