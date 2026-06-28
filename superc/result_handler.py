"""
预约结果处理模块

负责预约成功/失败后的副作用操作：
- 发送邮件通知
- 更新数据库状态
本地模式下跳过数据库操作。
"""

import logging
from datetime import datetime
from typing import Optional

from superc.email.notify_email import send_notify_email, send_update_email_notice

logger = logging.getLogger("main")


# ---------------------------------------------------------------------------
# Email notifications
# ---------------------------------------------------------------------------

def notify_booking_success(email: str, full_name: str, appointment_dt: Optional[datetime], location: str = "SuperC") -> None:
    """发送预约成功确认邮件"""
    try:
        appointment_info = {
            "name": full_name,
            "appointment_datetime": (appointment_dt.strftime("%Y-%m-%d %H:%M") if appointment_dt else "待确认"),
            "location": location,
        }
        sent = send_notify_email(email, appointment_info)
        if sent:
            logger.info(f"已向用户 {email} 发送预约确认邮件")
        else:
            logger.warning("邮件发送失败，但预约已成功完成")
    except Exception as e:
        logger.error(f"发送邮件通知时发生错误: {e}")


def notify_email_update_needed(email: str, full_name: str) -> None:
    """向用户发送邮箱更新提醒（账号被限制时）"""
    try:
        sent = send_update_email_notice(email, full_name)
        if sent:
            logger.info(f"已向用户 {email} 发送邮箱更新提醒邮件")
        else:
            logger.warning(f"邮箱更新提醒邮件发送失败: {email}")
    except Exception as e:
        logger.error(f"发送邮箱更新提醒邮件时发生异常: {e}")


# ---------------------------------------------------------------------------
# Database status updates
# ---------------------------------------------------------------------------

def mark_as_error(db_profile_id: Optional[int], full_name: str) -> None:
    """将用户状态标记为 error"""
    if db_profile_id is None:
        logger.info(f"[本地模式] 用户 {full_name} 状态标记为 error（无数据库更新）")
        return

    from db.utils import update_appointment_status
    try:
        success = update_appointment_status(db_profile_id, "error")
        if success:
            logger.info(f"已更新用户 {full_name} 的状态为 'error'")
        else:
            logger.error("更新用户状态为error失败")
    except Exception as e:
        logger.error(f"更新数据库状态时发生错误: {e}")


def mark_as_booked(db_profile_id: Optional[int], full_name: str, appointment_dt: Optional[datetime]) -> None:
    """将用户状态标记为 booked"""
    if db_profile_id is None:
        logger.info(f"[本地模式] 用户 {full_name} 预约成功！状态标记为 booked（无数据库更新）")
        return

    from db.utils import update_appointment_status
    try:
        success = update_appointment_status(db_profile_id, "booked", appointment_dt)
        if success:
            if appointment_dt:
                logger.info(f"已更新用户 {full_name} 的状态为 'booked'，预约时间: {appointment_dt.strftime('%Y-%m-%d %H:%M')}")
            else:
                logger.info(f"已更新用户 {full_name} 的状态为 'booked'")
        else:
            logger.error("更新用户状态失败，但预约已成功")
    except Exception as e:
        logger.error(f"更新数据库状态时发生错误: {e}")
