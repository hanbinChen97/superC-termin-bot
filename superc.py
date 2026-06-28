"""
主程序
# source .venv/bin/activate && python3 superc.py 2>&1
# nohup python3 superc.py 2>&1 | tee superc.log

source .venv/bin/activate && 

nohup uv run superc.py >> superc.log 2>&1 &

ps aux | grep superc.py

# 本地模式（不连接数据库）:
# python superc.py --local
"""
import logging
import sys
import time
import os
import argparse
from datetime import datetime
from typing import Optional, List

from superc.appointment_checker import run_check
from superc.config import LOCATIONS
from superc.utils.logging_utils import setup_logging
# 导入Profile类
from superc.profile import Profile
# 导入邮件通知模块
from superc.email.notify_email import send_notify_email, send_update_email_notice


# --- CLI argument parsing (early, before setup_logging) ---

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="SuperC 预约检查程序")
    parser.add_argument(
        "--local", "-l",
        action="store_true",
        help="本地模式：从 data/local_user.yaml 读取用户信息，不连接数据库"
    )
    return parser.parse_args()


# 解析参数并根据模式配置日志
_args = parse_args()
LOCAL_MODE = _args.local

if LOCAL_MODE:
    from superc import config as _superc_config
    _superc_config.ENABLE_SUPABASE_LOGS = False

setup_logging()

main_logger = logging.getLogger("main")
main_logger.setLevel(logging.INFO)

# --- Local mode helpers ---


def load_local_profiles() -> List[Profile]:
    """从 data/local_user.yaml 加载本地用户配置"""
    import yaml
    
    yaml_path = os.path.join(os.path.dirname(__file__), "data", "local_user.yaml")
    if not os.path.exists(yaml_path):
        main_logger.error(f"本地用户配置文件不存在: {yaml_path}")
        return []
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    if not data or "users" not in data or not data["users"]:
        main_logger.error("local_user.yaml 中没有用户数据")
        return []
    
    profiles = []
    for user in data["users"]:
        profile = Profile(
            vorname=user.get("vorname", ""),
            nachname=user.get("nachname", ""),
            email=user.get("email", ""),
            phone=user.get("phone", ""),
            geburtsdatum_day=user.get("geburtsdatum_day", 1),
            geburtsdatum_month=user.get("geburtsdatum_month", 1),
            geburtsdatum_year=user.get("geburtsdatum_year", 1990),
            preferred_locations=user.get("preferred_locations", "superc"),
        )
        profiles.append(profile)
    
    main_logger.info(f"从本地文件加载了 {len(profiles)} 个用户")
    return profiles



def log_profile_info(profile):
    """将Profile信息输出到日志"""
    main_logger.info("=== Profile 信息 ===")
    main_logger.info(f"姓名: {profile.full_name}")
    main_logger.info(f"邮箱: {profile.email}")
    main_logger.info(f"电话: {profile.phone}")
    main_logger.info(f"生日: {profile.geburtsdatum_day}/{profile.geburtsdatum_month}/{profile.geburtsdatum_year}")
    main_logger.info(f"偏好地点: {profile.preferred_locations}")
    main_logger.info("-" * 30)

def setup_current_profile(local_mode=False):
    """
    获取当前应该处理的用户profile
    
    Args:
        local_mode: 是否使用本地模式
    
    Returns:
        tuple: (db_profile, Profile) 如果找到用户，否则返回 (None, None)
              本地模式下 db_profile 为 None
    """
    if local_mode:
        profiles = load_local_profiles()
        if profiles:
            profile = profiles[0]
            main_logger.info(f"[本地模式] 当前处理用户: {profile.full_name}")
            profile.print_info()
            log_profile_info(profile)
            return None, profile
        else:
            main_logger.info("本地用户配置为空")
            return None, None
    
    # 数据库模式
    from db.utils import get_first_waiting_profile
    try:
        db_profile = get_first_waiting_profile()
        if db_profile:
            # parse db_profile to appointment Profile object
            profile = Profile.from_db_record(db_profile)
            main_logger.info(f"当前处理用户: {profile.full_name} (ID: {db_profile.id})")
            profile.print_info()
            log_profile_info(profile)
            return db_profile, profile
        else:
            main_logger.info("等待队列为空，暂无用户进行检查")
            return None, None
    except Exception as e:
        main_logger.error(f"获取数据库profile失败: {e}")
        return None, None

def send_update_email_to_user(email: str, full_name: str) -> None:
    """
    向用户发送邮箱更新提醒邮件
    
    Args:
        email: 用户邮箱地址
        full_name: 用户全名
    
    Returns:
        None
    """
    try:
        sent = send_update_email_notice(email, full_name)
        if sent:
            main_logger.info(f"已向用户 {email} 发送邮箱更新提醒邮件")
        else:
            main_logger.warning(f"邮箱更新提醒邮件发送失败: {email}")
    except Exception as e:
        main_logger.error(f"发送邮箱更新提醒邮件时发生异常: {e}")

def update_profile_status_to_error(db_profile_id: int, full_name: str) -> None:
    """
    更新数据库profile状态为error
    
    Args:
        db_profile_id: 数据库profile的ID
        full_name: 用户全名
    
    Returns:
        None
    """
    if db_profile_id is None:
        main_logger.info(f"[本地模式] 用户 {full_name} 状态标记为 error（无数据库更新）")
        return
    from db.utils import update_appointment_status
    try:
        success = update_appointment_status(db_profile_id, 'error')
        if success:
            main_logger.info(f"已更新用户 {full_name} 的状态为 'error'")
        else:
            main_logger.error("更新用户状态为error失败")
    except Exception as e:
        main_logger.error(f"更新数据库状态时发生错误: {e}")

def send_appointment_confirmation_email(email: str, full_name: str, appointment_dt: Optional[datetime], location: str = 'SuperC') -> None:
    """
    发送预约确认邮件
    
    Args:
        email: 用户邮箱地址
        full_name: 用户全名
        appointment_dt: 预约时间
        location: 预约地点，默认为'SuperC'
    
    Returns:
        None
    """
    try:
        appointment_info = {
            'name': full_name,
            'appointment_datetime': (appointment_dt.strftime("%Y-%m-%d %H:%M") if appointment_dt else '待确认'),
            'location': location
        }
        email_sent = send_notify_email(email, appointment_info)
        if email_sent:
            main_logger.info(f"已向用户 {email} 发送预约确认邮件")
        else:
            main_logger.warning(f"邮件发送失败，但预约已成功完成")
    except Exception as e:
        main_logger.error(f"发送邮件通知时发生错误: {e}")

def update_profile_status_to_booked(db_profile_id: int, full_name: str, appointment_dt: Optional[datetime]) -> None:
    """
    更新数据库profile状态为booked
    
    Args:
        db_profile_id: 数据库profile的ID
        full_name: 用户全名
        appointment_dt: 预约时间
    
    Returns:
        None
    """
    if db_profile_id is None:
        main_logger.info(f"[本地模式] 用户 {full_name} 预约成功！状态标记为 booked（无数据库更新）")
        return
    from db.utils import update_appointment_status
    try:
        success = update_appointment_status(db_profile_id, 'booked', appointment_dt)  # type: ignore[arg-type]
        if success:
            if appointment_dt:
                formatted_dt = appointment_dt.strftime("%Y-%m-%d %H:%M")
                main_logger.info(f"已更新用户 {full_name} 的状态为 'booked'，预约时间: {formatted_dt}")
            else:
                main_logger.info(f"已更新用户 {full_name} 的状态为 'booked'")
        else:
            main_logger.error(f"更新用户状态失败，但预约已成功")
    except Exception as e:
        main_logger.error(f"更新数据库状态时发生错误: {e}")

def get_next_user_profile(local_mode=False):
    """获取下一个等待中的用户profile，返回(db_profile, profile)或(None, None)"""
    if local_mode:
        # 本地模式只有一个用户，处理完就结束
        main_logger.info("[本地模式] 没有更多用户")
        return None, None
    
    from db.utils import get_first_waiting_profile
    try:
        next_db_profile = get_first_waiting_profile()
        
        if next_db_profile:
            next_profile = Profile.from_db_record(next_db_profile)
            main_logger.info(f"找到下一个用户: {next_profile.full_name} (ID: {next_db_profile.id})")
            next_profile.print_info()
            log_profile_info(next_profile)
            return next_db_profile, next_profile
        else:
            main_logger.info("没有更多等待的用户")
            return None, None
    except Exception as e:
        main_logger.error(f"获取下一个用户profile失败: {e}")
        return None, None

if __name__ == "__main__":
    local_mode = LOCAL_MODE
    
    mode_label = "[本地模式]" if local_mode else ""
    main_logger.info(f"启动 SupaC 预约检查程序{mode_label}，进程PID: {os.getpid()}")
    
    superc_config = LOCATIONS["superc"]

    # 获取当前应该处理的用户profile
    current_db_profile, current_profile = setup_current_profile(local_mode=local_mode)
    
    if not current_profile:
        main_logger.info("No profiles to process, exiting.")
        sys.exit(0)


    while True:
        # 检查当前时间，如果是凌晨 1 点 以后，也就是改成等于 2
        current_hour = datetime.now().hour
        if current_hour == 1:
            main_logger.info("已到凌晨 1 点，程序自动退出")
            break
            
        try:
            has_appointment, message, appointment_dt = run_check(superc_config, current_profile)

            # 无预约时等待1分钟后重新检查
            if not has_appointment:
                # main_logger.info(message)
                time.sleep(60)
                continue

            # -------------- 有预约时的处理逻辑 --------------
            # 处理完成标志
            should_get_next_user = False

            if message == "superC server error":
                main_logger.warning("检测到superC server error，等待60秒后重试")
                time.sleep(60)
                continue
            
            # 情况1: "zu vieler Terminanfragen" 错误
            if "zu vieler Terminanfragen" in message:
                main_logger.error(f"检测到错误: 提交过于频繁 (关键词: zu vieler Terminanfragen)")

                # 向用户发送邮箱更新提醒邮件（提示更新邮箱，不提及被系统 block）
                if current_profile:
                    send_update_email_to_user(current_profile.email, current_profile.full_name)

                # 更新数据库profile状态为error
                if current_profile:
                    db_id = current_db_profile.id if current_db_profile else None
                    update_profile_status_to_error(db_id, current_profile.full_name)

                should_get_next_user = True
                
            # 情况2: 预约成功
            if "预约已完成" in message :
                main_logger.info(f"成功！ {message}")
                
                # 发送邮件通知
                if current_profile:
                    send_appointment_confirmation_email(current_profile.email, current_profile.full_name, appointment_dt, location='SuperC')

                # 更新数据库profile状态为booked
                if current_profile:
                    db_id = current_db_profile.id if current_db_profile else None
                    update_profile_status_to_booked(db_id, current_profile.full_name, appointment_dt)
                
                should_get_next_user = True
            
            # 统一处理：获取下一个用户
            if should_get_next_user:
                main_logger.info("处理完成！立即检查是否有下一个用户需要处理...")
                current_db_profile, current_profile = get_next_user_profile(local_mode=local_mode)
                
                if current_db_profile and current_profile:
                    main_logger.info("继续查询下一个用户的预约...")
                    continue
                elif current_profile:
                    # 本地模式下 db_profile 为 None 但 profile 存在
                    main_logger.info("继续查询下一个用户的预约...")
                    continue
                else:
                    main_logger.info("没有更多等待的用户，程序退出")
                    break


            main_logger.warning(f"出现未预期的消息: {message}")
        except Exception as e:
            main_logger.error(f"检查过程中发生未预料的错误: {e}", exc_info=True)

        
