#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试验证脚本

用于快速验证集成测试是否正常工作
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def quick_test():
    """快速测试主要功能"""
    print("🚀 开始快速测试验证...")
    
    try:
        # 1. 测试环境变量加载
        print("\n1. 测试环境变量加载...")
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            print(f"❌ 缺少环境变量: {missing}")
            return False
        else:
            print("✅ 环境变量检查通过")
        
        # 2. 测试数据库连接
        print("\n2. 测试数据库连接...")
        from db.utils import engine
        from sqlalchemy import text
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if result:
                print("✅ 数据库连接成功")
            else:
                print("❌ 数据库连接失败")
                return False
        
        # 3. 测试数据库工具函数
        print("\n3. 测试数据库工具函数...")
        from db.utils import get_waiting_queue_count, get_first_waiting_profile
        
        count = get_waiting_queue_count()
        first_profile = get_first_waiting_profile()
        
        print(f"✅ 等待队列长度: {count}")
        if first_profile:
            print(f"✅ 队列第一名: {first_profile.vorname} {first_profile.nachname}")
        else:
            print("✅ 当前队列为空")
        
        # 4. 测试 SuperC 组件导入
        print("\n4. 测试 SuperC 组件导入...")
        from superc.config import LOCATIONS, LOG_FORMAT
        from superc.appointment_checker import run_check
        from superc.profile import Profile
        
        if "superc" in LOCATIONS and callable(run_check):
            print("✅ SuperC 组件导入成功")
        else:
            print("❌ SuperC 组件导入失败")
            return False
        
        print("\n🎉 所有快速测试通过！")
        print("\n可以运行完整的集成测试:")
        print("  python tests/run_integration_tests.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 快速测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1) 