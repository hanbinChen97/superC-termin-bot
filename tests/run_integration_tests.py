# -*- coding: utf-8 -*-
"""
集成测试运行器

运行所有集成测试，包括：
- 数据库集成测试 (db/utils.py main() 函数)
- SuperC 主程序集成测试 (superc.py 主逻辑)

使用方法:
    python tests/run_integration_tests.py
    python tests/run_integration_tests.py --database-only
    python tests/run_integration_tests.py --superc-only
    python tests/run_integration_tests.py --check-env
"""

import sys
import os
import argparse
import unittest
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_environment():
    """检查环境变量配置"""
    print("=" * 60)
    print("检查环境变量配置")
    print("=" * 60)
    
    load_dotenv()
    
    required_env_vars = [
        "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"
    ]
    
    missing_vars = []
    present_vars = []
    
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            present_vars.append(var)
            # 对于密码类变量，只显示前几个字符
            if "PASSWORD" in var and len(value) > 3:
                display_value = value[:3] + "***"
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
        else:
            missing_vars.append(var)
            print(f"❌ {var}: 未设置")
    
    print(f"\n总结: {len(present_vars)}/{len(required_env_vars)} 个环境变量已配置")
    
    if missing_vars:
        print(f"❌ 缺少环境变量: {missing_vars}")
        print("请确保 .env 文件存在并包含所有必要的配置")
        return False
    else:
        print("✓ 所有必要的环境变量都已配置")
        return True


def run_database_tests():
    """运行数据库集成测试"""
    try:
        from tests.integration.test_database_integration import run_database_integration_tests
        return run_database_integration_tests()
    except ImportError as e:
        print(f"❌ 无法导入数据库测试: {e}")
        return False


def run_superc_tests():
    """运行 SuperC 集成测试"""
    try:
        from tests.integration.test_superc_integration import run_superc_integration_tests
        return run_superc_integration_tests()
    except ImportError as e:
        print(f"❌ 无法导入 SuperC 测试: {e}")
        return False


def run_all_integration_tests():
    """运行所有集成测试"""
    print("=" * 80)
    print("开始运行所有集成测试")
    print("=" * 80)
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，跳过集成测试")
        return False
    
    all_passed = True
    
    # 运行数据库测试
    print("\n" + "=" * 60)
    print("1. 运行数据库集成测试")
    print("=" * 60)
    db_result = run_database_tests()
    if not db_result:
        all_passed = False
        print("❌ 数据库集成测试失败")
    else:
        print("✓ 数据库集成测试通过")
    
    # 运行 SuperC 测试
    print("\n" + "=" * 60)
    print("2. 运行 SuperC 集成测试")
    print("=" * 60)
    superc_result = run_superc_tests()
    if not superc_result:
        all_passed = False
        print("❌ SuperC 集成测试失败")
    else:
        print("✓ SuperC 集成测试通过")
    
    # 总结
    print("\n" + "=" * 80)
    print("集成测试总结")
    print("=" * 80)
    print(f"数据库测试: {'✓ 通过' if db_result else '❌ 失败'}")
    print(f"SuperC 测试: {'✓ 通过' if superc_result else '❌ 失败'}")
    print(f"整体结果: {'✓ 所有测试通过' if all_passed else '❌ 有测试失败'}")
    
    return all_passed


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行集成测试')
    parser.add_argument('--database-only', action='store_true', 
                      help='只运行数据库集成测试')
    parser.add_argument('--superc-only', action='store_true',
                      help='只运行 SuperC 集成测试')
    parser.add_argument('--check-env', action='store_true',
                      help='只检查环境变量配置')
    
    args = parser.parse_args()
    
    if args.check_env:
        success = check_environment()
        sys.exit(0 if success else 1)
    
    if args.database_only:
        print("运行数据库集成测试...")
        if not check_environment():
            sys.exit(1)
        success = run_database_tests()
        sys.exit(0 if success else 1)
    
    if args.superc_only:
        print("运行 SuperC 集成测试...")
        if not check_environment():
            sys.exit(1)
        success = run_superc_tests()
        sys.exit(0 if success else 1)
    
    # 默认运行所有测试
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 