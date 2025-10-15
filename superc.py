"""
主程序
# source .venv/bin/activate && python3 superc.py 2>&1
# nohup python3 superc.py 2>&1 | tee superc.log

source .venv/bin/activate && 

nohup python3 superc.py >> superc.log 2>&1 &

ps aux | grep superc.py
"""
import logging
import time
import os
from datetime import datetime
from typing import Optional

from superc.appointment_checker import run_check
from superc.config import LOCATIONS
from superc.logging_utils import setup_logging
# 导入数据库工具模块
from db.utils import get_first_waiting_profile, update_appointment_status
# 导入Profile类
from superc.profile import Profile
# 导入邮件通知模块
from superc.notify_email import send_notify_email, send_update_email_notice

setup_logging()

main_logger = logging.getLogger("main")
main_logger.setLevel(logging.INFO)



def log_profile_info(profile):
    """将Profile信息输出到日志"""
    main_logger.info("=== Profile 信息 ===")
    main_logger.info(f"姓名: {profile.full_name}")
    main_logger.info(f"邮箱: {profile.email}")
    main_logger.info(f"电话: {profile.phone}")
    main_logger.info(f"生日: {profile.geburtsdatum_day}/{profile.geburtsdatum_month}/{profile.geburtsdatum_year}")
    main_logger.info(f"偏好地点: {profile.preferred_locations}")
    main_logger.info("-" * 30)

def get_next_user_profile():
    """获取下一个等待中的用户profile，返回(db_profile, profile)或(None, None)"""
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
    main_logger.info(f"启动 SuperC 预约检查程序，进程PID: {os.getpid()}")
    
    superc_config = LOCATIONS["superc"]

    # 获取当前应该处理的用户profile
    current_db_profile = None
    current_profile: Optional[Profile] = None

    
    try:
        current_db_profile = get_first_waiting_profile()
        if current_db_profile:
            current_profile = Profile.from_db_record(current_db_profile)
            main_logger.info(f"当前处理用户: {current_profile.full_name} (ID: {current_db_profile.id})")
            current_profile.print_info()
            log_profile_info(current_profile)
        else:
            main_logger.info("等待队列为空，暂无用户进行检查")
    except Exception as e:
        main_logger.error(f"获取数据库profile失败: {e}")
        current_db_profile = None
        current_profile = None


    while True:
        # 检查当前时间，如果是凌晨 1 点 以后，也就是改成等于 2
        current_hour = datetime.now().hour
        if current_hour == 1:
            main_logger.info("已到凌晨 1 点，程序自动退出")
            break
            
        try:
            has_appointment, message, appointment_datetime_str = run_check(superc_config, current_profile)

            # 无预约时等待1分钟后重新检查
            if not has_appointment:
                # main_logger.info(message)
                time.sleep(60)
                continue

            # 有预约时，根据message分情况处理
            if has_appointment:
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
                        try:
                            sent = send_update_email_notice(current_profile.email, current_profile.full_name)
                            if sent:
                                main_logger.info(f"已向用户 {current_profile.email} 发送邮箱更新提醒邮件")
                            else:
                                main_logger.warning(f"邮箱更新提醒邮件发送失败: {current_profile.email}")
                        except Exception as e:
                            main_logger.error(f"发送邮箱更新提醒邮件时发生异常: {e}")

                    # 更新数据库profile状态为error
                    if current_db_profile:
                        try:
                            success = update_appointment_status(current_db_profile.id, 'error')  # type: ignore
                            if success and current_profile:
                                main_logger.info(f"已更新用户 {current_profile.full_name} 的状态为 'error'")
                            else:
                                main_logger.error("更新用户状态为error失败")
                        except Exception as e:
                            main_logger.error(f"更新数据库状态时发生错误: {e}")

                    should_get_next_user = True
                    
                # 情况2: 预约成功
                if "预约已完成" in message :
                    main_logger.info(f"成功！ {message}")
                    
                    # 更新数据库profile状态为booked
                    if current_db_profile:
                        try:
                            success = update_appointment_status(current_db_profile.id, 'booked', appointment_datetime_str)  # type: ignore
                            if success and current_profile:
                                if appointment_datetime_str:
                                    main_logger.info(f"已更新用户 {current_profile.full_name} 的状态为 'booked'，预约时间: {appointment_datetime_str}")
                                else:
                                    main_logger.info(f"已更新用户 {current_profile.full_name} 的状态为 'booked'")
                                
                                # 发送邮件通知
                                try:
                                    appointment_info = {
                                        'name': current_profile.full_name,
                                        'appointment_datetime': appointment_datetime_str or '待确认',
                                        'location': 'SuperC'
                                    }
                                    email_sent = send_notify_email(current_profile.email, appointment_info)
                                    if email_sent:
                                        main_logger.info(f"已向用户 {current_profile.email} 发送预约确认邮件")
                                    else:
                                        main_logger.warning(f"邮件发送失败，但预约已成功完成")
                                except Exception as e:
                                    main_logger.error(f"发送邮件通知时发生错误: {e}")
                            else:
                                main_logger.error(f"更新用户状态失败，但预约已成功")
                        except Exception as e:
                            main_logger.error(f"更新数据库状态时发生错误: {e}")
                    
                    should_get_next_user = True
                
                # 统一处理：获取下一个用户
                if should_get_next_user:
                    main_logger.info("处理完成！立即检查是否有下一个用户需要处理...")
                    current_db_profile, current_profile = get_next_user_profile()
                    
                    if current_db_profile and current_profile:
                        main_logger.info("继续查询下一个用户的预约...")
                        continue
                    else:
                        main_logger.info("没有更多等待的用户，程序退出")
                        break

            main_logger.warning(f"出现未预期的消息: {message}")
        except Exception as e:
            main_logger.error(f"检查过程中发生未预料的错误: {e}", exc_info=True)

        
