# -*- coding: utf-8 -*-
"""
数据库集成测试

测试 db/utils.py 的数据库连接和操作功能
依赖 .env 文件中的数据库配置
"""

import sys
import os
import unittest
from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from dotenv import load_dotenv


class TestDatabaseIntegration(unittest.TestCase):
    """数据库集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置 - 确保环境变量加载"""
        # 加载 .env 文件
        load_dotenv()
        
        # 检查必要的环境变量是否存在
        required_env_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            pytest.skip(f"缺少必要的环境变量: {missing_vars}")
    
    def test_database_utils_main_function(self):
        """测试 db/utils.py 的 main() 函数"""
        # 导入 db.utils 模块
        from db import utils as db_utils
        
        # 捕获输出
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        # 执行 main() 函数并捕获输出
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                db_utils.main()
            
            # 获取输出内容
            stdout_content = stdout_capture.getvalue()
            stderr_content = stderr_capture.getvalue()
            
            # 验证连接成功
            self.assertIn("Connection successful!", stdout_content, 
                         "数据库连接应该成功")
            
            # 验证等待队列统计信息输出
            self.assertIn("等待队列统计信息", stdout_content,
                         "应该输出等待队列统计信息")
            
            # 验证当前等待队列长度输出
            self.assertIn("当前等待队列长度:", stdout_content,
                         "应该输出当前等待队列长度")
            
            # 如果有错误输出，记录但不一定失败（可能是正常的警告）
            if stderr_content:
                print(f"警告/错误输出: {stderr_content}")
            
            print("✓ 数据库 main() 函数测试通过")
            
        except Exception as e:
            self.fail(f"执行 db/utils.py main() 函数失败: {e}")
    
    def test_database_connection_only(self):
        """仅测试数据库连接（不执行完整的 main() 函数）"""
        from db.utils import engine
        from sqlalchemy import text
        
        try:
            with engine.connect() as connection:
                # 执行简单查询验证连接 (SQLAlchemy 2.0+ 需要使用 text())
                result = connection.execute(text("SELECT 1"))
                self.assertIsNotNone(result, "数据库查询应该返回结果")
            
            print("✓ 数据库连接测试通过")
            
        except Exception as e:
            self.fail(f"数据库连接失败: {e}")
    
    def test_waiting_queue_functions(self):
        """测试等待队列相关函数"""
        from db.utils import get_waiting_queue_count, get_first_waiting_profile, get_all_waiting_profiles
        
        try:
            # 测试获取等待队列数量
            count = get_waiting_queue_count()
            self.assertIsInstance(count, int, "等待队列数量应该是整数")
            self.assertGreaterEqual(count, 0, "等待队列数量应该大于等于0")
            
            # 测试获取第一个等待用户
            first_profile = get_first_waiting_profile()
            # first_profile 可能为 None（队列为空），这是正常的
            
            # 测试获取所有等待用户
            all_waiting = get_all_waiting_profiles()
            self.assertIsInstance(all_waiting, list, "所有等待用户应该是列表")
            self.assertEqual(len(all_waiting), count, "等待用户列表长度应该等于队列数量")
            
            # 如果有等待用户，验证第一个用户
            if count > 0 and first_profile:
                self.assertEqual(first_profile.id, all_waiting[0].id, "第一个等待用户应该匹配")
                self.assertEqual(first_profile.appointment_status, 'waiting', "状态应该是 waiting")
            
            print(f"✓ 等待队列功能测试通过 (当前队列长度: {count})")
            
        except Exception as e:
            self.fail(f"等待队列功能测试失败: {e}")


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseIntegrationPytest:
    """使用 pytest 的数据库集成测试"""
    
    def test_db_main_with_pytest(self):
        """使用 pytest 测试 db/utils.py main() 函数"""
        from db import utils as db_utils
        
        # 使用 pytest 的 capsys 捕获输出
        import pytest
        
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            db_utils.main()
        
        stdout_content = stdout_capture.getvalue()
        
        assert "Connection successful!" in stdout_content
        assert "等待队列统计信息" in stdout_content


def run_database_integration_tests():
    """独立运行数据库集成测试的函数"""
    print("=" * 60)
    print("运行数据库集成测试")
    print("=" * 60)
    
    # 检查环境变量
    load_dotenv()
    required_env_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {missing_vars}")
        print("请确保 .env 文件存在并包含所有必要的数据库配置")
        return False
    
    print("✓ 环境变量检查通过")
    
    # 运行测试
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDatabaseIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # 直接运行时执行集成测试
    success = run_database_integration_tests()
    sys.exit(0 if success else 1) 