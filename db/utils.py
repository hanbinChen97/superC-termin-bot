"""
source .venv/bin/activate && python -m db.utils
数据库工具模块 - 提供预约配置文件的数据库操作功能
供 superc.py 和其他模块使用的纯工具模块
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os
from typing import List, Optional
from datetime import datetime
import re
from db.models import AppointmentProfile

# 数据库连接配置
def _init_database():
    """初始化数据库连接"""
    # Load environment variables from .env
    load_dotenv()
    
    # Fetch variables
    USER = os.getenv("DB_USER")
    PASSWORD = os.getenv("DB_PASSWORD")
    HOST = os.getenv("DB_HOST")
    PORT = os.getenv("DB_PORT")
    DBNAME = os.getenv("DB_NAME")
    
    # Construct the SQLAlchemy connection string
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
    
    # Create the SQLAlchemy engine
    engine = create_engine(DATABASE_URL)
    # If using Transaction Pooler or Session Pooler, we want to ensure we disable SQLAlchemy client side pooling -
    # https://docs.sqlalchemy.org/en/20/core/pooling.html#switching-pool-implementations
    # engine = create_engine(DATABASE_URL, poolclass=NullPool)
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal

# 初始化数据库连接
engine, SessionLocal = _init_database()

def parse_appointment_date(appointment_date_str: str) -> Optional[datetime]:
    """
    解析预约日期字符串，转换为datetime对象
    输入格式: "Donnerstag, 16.10.2025 11:00"
    输出: datetime对象
    """
    try:
        # 从 "Donnerstag, 16.10.2025 11:00" 中提取日期和时间部分
        # 去掉星期几，只保留日期和时间
        if ', ' in appointment_date_str:
            date_time_part = appointment_date_str.split(', ')[1]  # "16.10.2025 11:00"
        else:
            date_time_part = appointment_date_str
        
        # 解析日期时间: "16.10.2025 11:00"
        parsed_datetime = datetime.strptime(date_time_part, "%d.%m.%Y %H:%M")
        return parsed_datetime
        
    except (ValueError, IndexError) as e:
        print(f"无法解析预约日期 '{appointment_date_str}': {e}")
        return None

def get_all_appointment_profiles() -> List[AppointmentProfile]:
    """
    获取所有预约配置文件
    返回: 所有 AppointmentProfile 记录的列表
    """
    session = SessionLocal()
    try:
        profiles = session.query(AppointmentProfile).all()
        return profiles
    except Exception as e:
        print(f"查询失败: {e}")
        return []
    finally:
        session.close()

def get_first_waiting_profile() -> Optional[AppointmentProfile]:
    """
    获取等待队列中的第一个用户（排队最久的用户）
    使用 waiting_queue_idx 索引来优化查询性能
    只查询 appointment_status = 'waiting' 的记录，按 created_at 升序排列
    """
    session = SessionLocal()
    try:
        # 利用 waiting_queue_idx 索引：只查询等待状态的记录，按创建时间升序排列
        first_waiting_profile = session.query(AppointmentProfile)\
                                      .filter(AppointmentProfile.appointment_status == 'waiting')\
                                      .order_by(AppointmentProfile.created_at)\
                                      .first()
        return first_waiting_profile
    except Exception as e:
        print(f"查询失败: {e}")
        return None
    finally:
        session.close()

def update_appointment_status(profile_id: int, status: str, appointment_date: Optional[str] = None) -> bool:
    """
    更新预约配置文件的状态和预约日期
    参数:
        profile_id: 预约配置文件ID
        status: 新的状态值（如 'booked', 'error'）
        appointment_date: 预约日期字符串，格式如 "Donnerstag, 16.10.2025 11:00"
    返回: 更新是否成功
    """
    session = SessionLocal()
    try:
        # 查找指定ID的记录
        profile = session.query(AppointmentProfile).filter(AppointmentProfile.id == profile_id).first()
        if profile:
            # 使用 setattr 来避免类型检查问题
            setattr(profile, 'appointment_status', status)
            
            # 如果提供了预约日期，解析并存储
            if appointment_date:
                parsed_date = parse_appointment_date(appointment_date)
                if parsed_date:
                    setattr(profile, 'appointment_date', parsed_date)
                    print(f"成功解析并存储预约日期: {appointment_date} -> {parsed_date}")
                else:
                    print(f"预约日期解析失败: {appointment_date}")

            setattr(profile, 'completed_at', datetime.now())

            session.commit()
            
            print(f"成功更新ID {profile_id} 的状态为 '{status}'")
            return True
        else:
            print(f"未找到ID为 {profile_id} 的记录")
            return False
    except Exception as e:
        session.rollback()
        print(f"更新失败: {e}")
        return False
    finally:
        session.close()

def get_all_waiting_profiles() -> List[AppointmentProfile]:
    """
    获取所有等待中的预约配置文件，按排队顺序排列
    使用 waiting_queue_idx 索引来优化查询性能
    """
    session = SessionLocal()
    try:
        # 利用 waiting_queue_idx 索引：只查询等待状态的记录，按创建时间升序排列
        waiting_profiles = session.query(AppointmentProfile)\
                                 .filter(AppointmentProfile.appointment_status == 'waiting')\
                                 .order_by(AppointmentProfile.created_at)\
                                 .all()
        return waiting_profiles
    except Exception as e:
        print(f"查询失败: {e}")
        return []
    finally:
        session.close()

def get_waiting_queue_count() -> int:
    """
    获取等待队列的长度
    使用 waiting_queue_idx 索引来优化查询性能
    """
    session = SessionLocal()
    try:
        # 利用 waiting_queue_idx 索引：只统计等待状态的记录数量
        count = session.query(AppointmentProfile)\
                      .filter(AppointmentProfile.appointment_status == 'waiting')\
                      .count()
        return count
    except Exception as e:
        print(f"查询失败: {e}")
        return 0
    finally:
        session.close()

def print_first_waiting_profile() -> None:
    """
    输出等待队列中第一个（排队最久的）用户信息
    """
    profile = get_first_waiting_profile()
    
    if not profile:
        print("等待队列为空")
        return
    
    print("=== 等待队列第一名（排队最久的用户） ===")
    print(f"ID: {profile.id}")
    print(f"用户ID: {profile.user_id}")
    print(f"姓名: {profile.vorname} {profile.nachname}")
    print(f"邮箱: {profile.email}")
    print(f"电话: {profile.phone}")
    print(f"生日: {profile.geburtsdatum_day}/{profile.geburtsdatum_month}/{profile.geburtsdatum_year}")
    print(f"偏好地点: {profile.preferred_locations}")
    print(f"预约状态: {profile.appointment_status}")
    print(f"预约日期: {profile.appointment_date}")
    print(f"地点类型: {profile.location_type}")
    print(f"创建时间: {profile.created_at}")
    print(f"更新时间: {profile.updated_at}")
    print("-" * 50)

def print_all_profiles() -> None:
    """
    打印所有预约配置文件的详细信息
    """
    profiles = get_all_appointment_profiles()
    
    if not profiles:
        print("没有找到任何预约配置文件")
        return
    
    print(f"总共找到 {len(profiles)} 个预约配置文件:\n")
    
    for profile in profiles:
        print(f"ID: {profile.id}")
        print(f"用户ID: {profile.user_id}")
        print(f"姓名: {profile.vorname} {profile.nachname}")
        print(f"邮箱: {profile.email}")
        print(f"电话: {profile.phone}")
        print(f"生日: {profile.geburtsdatum_day}/{profile.geburtsdatum_month}/{profile.geburtsdatum_year}")
        print(f"偏好地点: {profile.preferred_locations}")
        print(f"预约状态: {profile.appointment_status}")
        print(f"预约日期: {profile.appointment_date}")
        print(f"地点类型: {profile.location_type}")
        print(f"创建时间: {profile.created_at}")
        print(f"更新时间: {profile.updated_at}")
        print("-" * 50)

def main():
    """测试数据库连接和功能的主函数"""
    # Test the connection
    try:
        with engine.connect() as connection:
            print("Connection successful!")
            
        # 测试等待队列相关功能（使用 waiting_queue_idx 索引）
        print("\n=== 等待队列统计信息 ===")
        waiting_count = get_waiting_queue_count()
        print(f"当前等待队列长度: {waiting_count}")
        
        # 测试查询等待队列中的第一个用户（排队最久的用户）
        print("\n=== 查询等待队列第一名（使用 waiting_queue_idx 索引）===")
        first_waiting_profile = get_first_waiting_profile()
        print_first_waiting_profile()
        
        # 如果找到了等待中的用户，演示更新状态为 'booked'
        # if first_waiting_profile:
        #     print(f"\n=== 为等待队列第一名（ID: {first_waiting_profile.id}）预约成功 ===")
            # success = update_appointment_status(first_waiting_profile.id, 'booked')
            # if success:
            #     print("状态更新成功！队列第一名已完成预约")
                
            #     # 再次查看等待队列状态
            #     print("\n=== 更新后的等待队列状态 ===")
            #     new_waiting_count = get_waiting_queue_count()
            #     print(f"更新后等待队列长度: {new_waiting_count}")
                
            #     new_first_waiting = get_first_waiting_profile()
            #     if new_first_waiting:
            #         print(f"新的队列第一名: {new_first_waiting.vorname} {new_first_waiting.nachname} (ID: {new_first_waiting.id})")
            #     else:
            #         print("等待队列已空")
        
        # 测试查询所有预约配置文件
        # print("\n=== 查询所有预约配置文件 ===")
        # print_all_profiles()
            
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    main()