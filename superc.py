"""
主程序
# source .venv/bin/activate && python3 superc.py 2>&1
# nohup python3 superc.py 2>&1 | tee superc.log

source .venv/bin/activate && nohup python3 superc.py >> superc.log 2>&1 &
"""
import logging
import time
import os
import json
from datetime import datetime
from typing import Optional

from superc.appointment_checker import run_check
from superc.config import LOCATIONS, LOG_FORMAT
# 导入数据库工具模块
from db.utils import get_first_waiting_profile, update_appointment_status
# 导入Profile类
from superc.profile import Profile
# 导入config模块用于设置profile
from superc import config

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)



def log_profile_info(profile):
    """将Profile信息输出到日志"""
    logging.info("=== Profile 信息 ===")
    logging.info(f"姓名: {profile.full_name}")
    logging.info(f"邮箱: {profile.email}")
    logging.info(f"电话: {profile.phone}")
    logging.info(f"生日: {profile.geburtsdatum_day}/{profile.geburtsdatum_month}/{profile.geburtsdatum_year}")
    logging.info(f"偏好地点: {profile.preferred_locations}")
    logging.info("-" * 30)

def get_next_user_profile():
    """获取下一个等待中的用户profile，返回(db_profile, profile)或(None, None)"""
    try:
        next_db_profile = get_first_waiting_profile()
        
        if next_db_profile:
            next_profile = Profile.from_db_record(next_db_profile)
            logging.info(f"找到下一个用户: {next_profile.full_name} (ID: {next_db_profile.id})")
            next_profile.print_info()
            log_profile_info(next_profile)
            return next_db_profile, next_profile
        else:
            logging.info("没有更多等待的用户")
            return None, None
    except Exception as e:
        logging.error(f"获取下一个用户profile失败: {e}")
        return None, None

if __name__ == "__main__":
    logging.info(f"启动 SuperC 预约检查程序，进程PID: {os.getpid()}")
    superc_config = LOCATIONS["superc"]

    # 获取当前应该处理的用户profile
    current_db_profile = None
    current_profile: Optional[Profile] = None
    

    
    try:
        current_db_profile = get_first_waiting_profile()
        if current_db_profile:
            current_profile = Profile.from_db_record(current_db_profile)
            logging.info(f"当前处理用户: {current_profile.full_name} (ID: {current_db_profile.id})")
            current_profile.print_info()
            log_profile_info(current_profile)
        else:
            logging.info("等待队列为空，暂无用户进行检查")
    except Exception as e:
        logging.error(f"获取数据库profile失败: {e}")
        current_db_profile = None
        current_profile = None

    while True:
        # 检查当前时间，如果是凌晨 1 点 以后，也就是改成等于 2
        current_hour = datetime.now().hour
        if current_hour == 1:
            logging.info("已到凌晨 1 点，程序自动退出")
            break
            
        try:
            has_appointment, message, appointment_datetime_str = run_check(superc_config, current_profile)

            # 无预约时等待1分钟后重新检查
            if not has_appointment:
                # logging.info(message)
                time.sleep(60)
                continue

            # 有预约时，根据message分情况处理
            if has_appointment:
                # 处理完成标志
                should_get_next_user = False
                
                # 情况1: "zu vieler Terminanfragen" 错误
                if "zu vieler Terminanfragen" in message or "提交过于频繁，请稍后再试" in message:
                    logging.error(f"检测到错误: 提交过于频繁，请稍后再试 (关键词: zu vieler Terminanfragen)")
                    
                    # 更新数据库profile状态为error
                    if current_db_profile:
                        try:
                            success = update_appointment_status(current_db_profile.id, 'error')  # type: ignore
                            if success and current_profile:
                                logging.info(f"已更新用户 {current_profile.full_name} 的状态为 'error'")
                            else:
                                logging.error(f"更新用户状态为error失败")
                        except Exception as e:
                            logging.error(f"更新数据库状态时发生错误: {e}")
                    
                    should_get_next_user = True
                    
                # 情况2: 预约成功
                else:
                    logging.info(f"成功！ {message}")
                    
                    # 更新数据库profile状态为booked
                    if current_db_profile:
                        try:
                            success = update_appointment_status(current_db_profile.id, 'booked', appointment_datetime_str)  # type: ignore
                            if success and current_profile:
                                if appointment_datetime_str:
                                    logging.info(f"已更新用户 {current_profile.full_name} 的状态为 'booked'，预约时间: {appointment_datetime_str}")
                                else:
                                    logging.info(f"已更新用户 {current_profile.full_name} 的状态为 'booked'")
                            else:
                                logging.error(f"更新用户状态失败，但预约已成功")
                        except Exception as e:
                            logging.error(f"更新数据库状态时发生错误: {e}")
                    
                    should_get_next_user = True
                
                # 统一处理：获取下一个用户
                if should_get_next_user:
                    logging.info("处理完成！立即检查是否有下一个用户需要处理...")
                    current_db_profile, current_profile = get_next_user_profile()
                    
                    if current_db_profile and current_profile:
                        logging.info("继续查询下一个用户的预约...")
                        continue
                    else:
                        logging.info("没有更多等待的用户，程序退出")
                        break

            logging.warning(f"出现未预期的消息: {message}")
        except Exception as e:
            logging.error(f"检查过程中发生未预料的错误: {e}", exc_info=True)

        