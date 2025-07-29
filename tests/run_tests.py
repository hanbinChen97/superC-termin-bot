# -*- coding: utf-8 -*-
"""
Test runner for the SuperC Termin Bot test suite.

Usage:
    python tests/run_tests.py                    # 运行基础单元测试
    python tests/run_tests.py --all             # 运行所有测试（包括集成测试）
    python tests/run_tests.py --integration     # 只运行集成测试
    python tests/run_tests.py --unit            # 只运行单元测试
    
Or run specific test files:
    python tests/test_config.py
    python tests/test_integration.py
"""

import sys
import os
import unittest
import argparse

# Add the parent directory to the path so we can import the superc package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_unit_tests():
    """Discover and run unit tests in the tests directory."""
    print("=" * 60)
    print("运行单元测试")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    # 只加载非集成测试目录中的测试
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_integration_tests():
    """Run integration tests."""
    print("=" * 60)
    print("运行集成测试")
    print("=" * 60)
    
    try:
        from tests.run_integration_tests import run_all_integration_tests
        return run_all_integration_tests()
    except ImportError as e:
        print(f"❌ 无法导入集成测试: {e}")
        return False


def run_all_tests():
    """Run both unit and integration tests."""
    print("=" * 80)
    print("运行所有测试（单元测试 + 集成测试）")
    print("=" * 80)
    
    unit_result = run_unit_tests()
    integration_result = run_integration_tests()
    
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"单元测试: {'✓ 通过' if unit_result else '❌ 失败'}")
    print(f"集成测试: {'✓ 通过' if integration_result else '❌ 失败'}")
    print(f"整体结果: {'✓ 所有测试通过' if (unit_result and integration_result) else '❌ 有测试失败'}")
    
    return unit_result and integration_result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SuperC Termin Bot 测试运行器')
    parser.add_argument('--all', action='store_true', 
                      help='运行所有测试（单元测试 + 集成测试）')
    parser.add_argument('--integration', action='store_true',
                      help='只运行集成测试')
    parser.add_argument('--unit', action='store_true',
                      help='只运行单元测试')
    
    args = parser.parse_args()
    
    if args.all:
        print("运行所有测试...")
        success = run_all_tests()
    elif args.integration:
        print("运行集成测试...")
        success = run_integration_tests()
    elif args.unit:
        print("运行单元测试...")
        success = run_unit_tests()
    else:
        # 默认只运行单元测试
        print("运行单元测试（默认）...")
        print("使用 --all 运行所有测试，--integration 运行集成测试")
        success = run_unit_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 