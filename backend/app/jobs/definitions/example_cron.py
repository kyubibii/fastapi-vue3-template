"""
示例：Cron 触发器任务

每天 02:00 执行，模拟日志清理或其他定时维护操作。
"""

import logging

logger = logging.getLogger(__name__)


async def run() -> None:
    """每天 02:00 执行的示例任务（Cron 触发器）。"""
    logger.info("[example_cron] 日志清理任务开始执行...")
    # TODO: 在此实现实际业务逻辑，例如清理过期审计日志
    logger.info("[example_cron] 日志清理任务执行完毕。")
