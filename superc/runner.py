"""
主循环调度模块

负责 "拿用户 → 检查预约 → 处理结果 → 下一个用户" 的循环逻辑。
不关心用户从哪来、结果怎么持久化，全部委托给 profile_loader 和 result_handler。
"""

import logging
import sys
import time
from datetime import datetime

from superc.appointment_checker import run_check
from superc.config import LOCATIONS
from superc.profile_loader import get_first_profile, get_next_profile
from superc import result_handler

logger = logging.getLogger("main")

# 轮询间隔（秒）
POLL_INTERVAL = 60
# 自动退出时间（小时）
AUTO_EXIT_HOUR = 1


def run(local_mode: bool = False) -> None:
    """程序主入口：加载用户并开始预约检查循环"""
    superc_config = LOCATIONS["superc"]

    # 获取第一个待处理用户
    current_db_profile, current_profile = get_first_profile(local_mode=local_mode)

    if not current_profile:
        logger.info("No profiles to process, exiting.")
        sys.exit(0)

    # 主循环
    while True:
        if datetime.now().hour == AUTO_EXIT_HOUR:
            logger.info(f"已到凌晨 {AUTO_EXIT_HOUR} 点，程序自动退出")
            break

        try:
            has_appointment, message, appointment_dt = run_check(superc_config, current_profile)

            # 无可用预约 → 等待后重试
            if not has_appointment:
                time.sleep(POLL_INTERVAL)
                continue

            # Server error → 等待后重试
            if message == "superC server error":
                logger.warning("检测到 superC server error，等待60秒后重试")
                time.sleep(POLL_INTERVAL)
                continue

            # ---------- 处理预约结果 ----------
            should_advance = _handle_result(
                message, appointment_dt, current_profile, current_db_profile
            )

            if should_advance:
                logger.info("处理完成！检查是否有下一个用户...")
                current_db_profile, current_profile = get_next_profile(local_mode=local_mode)
                if current_profile:
                    logger.info("继续查询下一个用户的预约...")
                    continue
                else:
                    logger.info("没有更多等待的用户，程序退出")
                    break

            # 未匹配任何已知结果
            logger.warning(f"出现未预期的消息: {message}")

        except Exception as e:
            logger.error(f"检查过程中发生未预料的错误: {e}", exc_info=True)


def _handle_result(message: str, appointment_dt, profile, db_profile) -> bool:
    """
    处理单次检查结果，返回是否应该切换到下一个用户。

    Returns:
        True  — 当前用户处理完毕，应获取下一个
        False — 未匹配已知结果类型
    """
    db_id = db_profile.id if db_profile else None

    # 情况1: 账号被限制（提交过于频繁）
    if "zu vieler Terminanfragen" in message:
        logger.error("检测到错误: 提交过于频繁 (zu vieler Terminanfragen)")
        result_handler.notify_email_update_needed(profile.email, profile.full_name)
        result_handler.mark_as_error(db_id, profile.full_name)
        return True

    # 情况2: 预约成功
    if "预约已完成" in message:
        logger.info(f"成功！ {message}")
        result_handler.notify_booking_success(profile.email, profile.full_name, appointment_dt, location="SuperC")
        result_handler.mark_as_booked(db_id, profile.full_name, appointment_dt)
        return True

    return False
