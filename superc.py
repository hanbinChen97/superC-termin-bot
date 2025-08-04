"""
主程序
"""

# source .venv/bin/activate && python3 superc.py 2>&1
# nohup python3 superc.py 2>&1 | tee superc.log

# source .venv/bin/activate && nohup python3 superc.py > superc.log 2>&1 &

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

def load_hanbin_profile(file_path: str = "data/hanbin") -> Optional[Profile]:
    """
    加载hanbin用户定义文件并转换为Profile对象
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # 从用户定义格式转换为Profile对象需要的数据
        profile_dict = {item['fuellen_in_name']: item['wert_zum_fuellen'] for item in profile_data}
        
        # 创建Profile对象
        hanbin_profile = Profile(
            vorname=profile_dict.get('vorname', ''),
            nachname=profile_dict.get('nachname', ''),
            email=profile_dict.get('email', ''),
            phone=profile_dict.get('phone', ''),
            geburtsdatum_day=int(profile_dict.get('geburtsdatumDay', 1)),
            geburtsdatum_month=int(profile_dict.get('geburtsdatumMonth', 1)),
            geburtsdatum_year=int(profile_dict.get('geburtsdatumYear', 1990)),
            preferred_locations=profile_dict.get('preferred_locations', 'superc')
        )
        
        return hanbin_profile
        
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        logging.error(f"无法读取hanbin profile文件 {file_path}: {e}")
        return None

def log_profile_info(profile):
    """将Profile信息输出到日志"""
    logging.info("=== Profile 信息 ===")
    logging.info(f"姓名: {profile.full_name}")
    logging.info(f"邮箱: {profile.email}")
    logging.info(f"电话: {profile.phone}")
    logging.info(f"生日: {profile.geburtsdatum_day}/{profile.geburtsdatum_month}/{profile.geburtsdatum_year}")
    logging.info(f"偏好地点: {profile.preferred_locations}")
    logging.info("-" * 30)

if __name__ == "__main__":
    logging.info(f"启动 SuperC 预约检查程序，进程PID: {os.getpid()}")
    superc_config = LOCATIONS["superc"]

    # 获取当前应该处理的用户profile
    current_db_profile = None
    current_profile: Optional[Profile] = None
    hanbin_profile: Optional[Profile] = None
    
    # 加载hanbin_profile (始终加载)
    hanbin_profile = load_hanbin_profile()
    if hanbin_profile:
        logging.info("已加载hanbin_profile")
    else:
        logging.warning("无法加载hanbin_profile")
    
    try:
        current_db_profile = get_first_waiting_profile()
        if current_db_profile:
            current_profile = Profile.from_appointment_profile(current_db_profile)
            logging.info(f"当前处理用户: {current_profile.full_name} (ID: {current_db_profile.id})")
            current_profile.print_info()
            log_profile_info(current_profile)
        else:
            logging.info("等待队列为空，仅使用hanbin profile进行检查")
    except Exception as e:
        logging.error(f"获取数据库profile失败: {e}")
        current_db_profile = None
        current_profile = None

    while True:
        # 检查当前时间，如果是22点或之后则退出
        # current_hour = datetime.now().hour
        # if current_hour >= 22:
        #     logging.info("已到22点，程序自动退出")
        #     break
            
        try:
            has_appointment, message = run_check(superc_config, current_profile, hanbin_profile)
            
            if has_appointment:
                logging.info(f"成功！ {message}")
                
                # 如果使用了数据库profile，更新其状态为booked
                if current_db_profile:
                    try:
                        success = update_appointment_status(current_db_profile.id, 'booked')  # type: ignore
                        if success and current_profile:
                            logging.info(f"已更新用户 {current_profile.full_name} 的状态为 'booked'")
                        else:
                            logging.error(f"更新用户状态失败，但预约已成功")
                    except Exception as e:
                        logging.error(f"更新数据库状态时发生错误: {e}")
                
                # 立即尝试获取下一个用户进行处理
                logging.info("预约成功！立即检查是否有下一个用户需要处理...")
                try:
                    next_db_profile = get_first_waiting_profile()
                    if next_db_profile:
                        current_db_profile = next_db_profile
                        current_profile = Profile.from_appointment_profile(current_db_profile)
                        logging.info(f"找到下一个用户: {current_profile.full_name} (ID: {current_db_profile.id})，继续查询预约...")
                        current_profile.print_info()
                        log_profile_info(current_profile)
                        continue  # 立即开始下一轮查询
                    else:
                        logging.info("没有更多等待的用户，程序退出")
                        break
                except Exception as e:
                    logging.error(f"获取下一个用户profile失败: {e}")
                    break  # 获取失败则退出

            if message == "表单提交失败, zu vieler Terminanfragen":
                logging.info(message)
                break  # 成功预约后退出循环
            
            if "当前没有可用预约时间" in message:
                # logging.info(message)
                
                # 等待1分钟后重新检查...
                time.sleep(60)
                continue  # 下一轮查询
            
            # 如果profile设置失败（例如预约时间不符合条件），继续下一轮
            if "无法设置合适的profile" in message:
                logging.info(f"跳过当前预约: {message}")
                continue

            logging.warning(f"出现未预期的消息: {message}")
        except Exception as e:
            logging.error(f"检查过程中发生未预料的错误: {e}", exc_info=True)

        