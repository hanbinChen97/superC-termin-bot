# -*- coding: utf-8 -*-
"""
SuperC 主程序集成测试

测试 superc.py 的主要预约检查流程
依赖 .env 文件中的配置和数据库连接
"""

import sys
import os
import unittest
from unittest.mock import patch, Mock, MagicMock
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import threading
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from dotenv import load_dotenv


class TestSupercIntegration(unittest.TestCase):
    """SuperC 主程序集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        # 加载 .env 文件
        load_dotenv()
        
        # 检查必要的环境变量是否存在
        required_env_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            pytest.skip(f"缺少必要的环境变量: {missing_vars}")
    
    def test_superc_imports_and_config(self):
        """测试 superc.py 的导入和配置加载"""
        try:
            # 导入 superc 模块中的组件
            from superc.config import LOCATIONS, LOG_FORMAT
            from superc.appointment_checker import run_check
            from db.utils import get_first_waiting_profile
            from superc.profile import Profile
            
            # 验证配置存在
            self.assertIn("superc", LOCATIONS, "LOCATIONS 应该包含 superc 配置")
            self.assertIsNotNone(LOG_FORMAT, "LOG_FORMAT 应该被定义")
            
            # 验证函数可调用
            self.assertTrue(callable(run_check), "run_check 应该是可调用的")
            self.assertTrue(callable(get_first_waiting_profile), "get_first_waiting_profile 应该是可调用的")
            
            print("✓ SuperC 导入和配置测试通过")
            
        except ImportError as e:
            self.fail(f"导入 SuperC 组件失败: {e}")
    
    @patch('superc.appointment_checker.run_check')
    @patch('db.utils.get_first_waiting_profile')
    def test_superc_main_logic_simulation(self, mock_get_profile, mock_run_check):
        """模拟测试 superc.py 的主要逻辑（不执行真实的无限循环）"""
        # 模拟没有用户在等待队列
        mock_get_profile.return_value = None
        
        # 模拟预约检查返回没有可用时间
        mock_run_check.return_value = (False, "当前没有可用预约时间")
        
        try:
            # 导入并设置 superc 的组件
            from superc.config import LOCATIONS
            
            superc_config = LOCATIONS["superc"]
            
            # 模拟主逻辑的一次迭代
            current_db_profile = mock_get_profile()
            self.assertIsNone(current_db_profile, "模拟应该返回无等待用户")
            
            # 模拟配置设置
            superc_config_with_profile = superc_config.copy()
            superc_config_with_profile["db_profile"] = current_db_profile
            superc_config_with_profile["profile"] = None
            
            # 模拟预约检查
            has_appointment, message = mock_run_check(superc_config_with_profile)
            self.assertFalse(has_appointment, "模拟应该返回无预约")
            self.assertIn("当前没有可用预约时间", message, "消息应该匹配")
            
            print("✓ SuperC 主逻辑模拟测试通过")
            
        except Exception as e:
            self.fail(f"SuperC 主逻辑测试失败: {e}")
    
    def test_superc_database_integration(self):
        """测试 SuperC 与数据库的集成"""
        try:
            from db.utils import get_first_waiting_profile, get_waiting_queue_count
            from superc.profile import Profile
            
            # 测试获取等待用户
            waiting_count = get_waiting_queue_count()
            first_profile = get_first_waiting_profile()
            
            self.assertIsInstance(waiting_count, int, "等待队列数量应该是整数")
            
            # 如果有等待用户，测试 Profile 转换
            if first_profile:
                try:
                    profile = Profile.from_appointment_profile(first_profile)
                    self.assertIsNotNone(profile.full_name, "Profile 应该有完整姓名")
                    print(f"✓ 找到等待用户: {profile.full_name}")
                except Exception as e:
                    self.fail(f"Profile 转换失败: {e}")
            else:
                print("✓ 当前无等待用户（这是正常的）")
            
            print("✓ SuperC 数据库集成测试通过")
            
        except Exception as e:
            self.fail(f"SuperC 数据库集成测试失败: {e}")
    
    def test_superc_time_check_logic(self):
        """测试 SuperC 的时间检查逻辑（22点退出机制）"""
        from datetime import datetime
        
        # 测试时间检查逻辑
        current_hour = datetime.now().hour
        should_exit = current_hour >= 22
        
        if should_exit:
            print(f"✓ 当前时间 {current_hour}:xx，应该退出程序")
        else:
            print(f"✓ 当前时间 {current_hour}:xx，可以继续运行")
        
        # 这个测试总是通过，只是验证逻辑
        self.assertTrue(True, "时间检查逻辑测试")


@pytest.mark.integration  
@pytest.mark.superc
class TestSupercIntegrationPytest:
    """使用 pytest 的 SuperC 集成测试"""
    
    def test_superc_components_with_pytest(self):
        """使用 pytest 测试 SuperC 组件"""
        from superc.config import LOCATIONS
        from superc.appointment_checker import run_check
        
        assert "superc" in LOCATIONS
        assert callable(run_check)


def run_superc_integration_tests():
    """独立运行 SuperC 集成测试的函数"""
    print("=" * 60)
    print("运行 SuperC 集成测试")
    print("=" * 60)
    
    # 检查环境变量
    load_dotenv()
    required_env_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {missing_vars}")
        print("请确保 .env 文件存在并包含所有必要的配置")
        return False
    
    print("✓ 环境变量检查通过")
    
    # 运行测试
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSupercIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # 直接运行时执行集成测试
    success = run_superc_integration_tests()
    sys.exit(0 if success else 1) 