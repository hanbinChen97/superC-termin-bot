#!/usr/bin/env python3
"""
数据库迁移脚本 - 专门管理 app_logs_min 表
直接执行 DDL 语句来创建和更新 app_logs_min 表

使用方法:
    python -m db.migrate            # 创建 app_logs_min 表
    python -m db.migrate --rollback  # 删除 app_logs_min 表
    python -m db.migrate --check     # 检查 app_logs_min 表是否存在
    python -m db.migrate --update    # 更新 app_logs_min 表结构
"""

import argparse
import sys
from typing import List
from sqlalchemy import text, inspect
from dotenv import load_dotenv

from db.utils import engine
from db.ddl_app_logs_min import ALL_DDL_STATEMENTS, ROLLBACK_DDL_STATEMENTS, UPDATE_DDL_STATEMENTS
from db.models import AppLogsMin


def execute_ddl_statements(statements: List[str], description: str = "DDL") -> bool:
    """
    执行 DDL 语句列表
    
    Args:
        statements: DDL 语句列表
        description: 操作描述
        
    Returns:
        bool: 执行是否成功
    """
    try:
        with engine.begin() as connection:
            print(f"开始执行 {description}...")
            
            for i, statement in enumerate(statements, 1):
                print(f"  执行语句 {i}/{len(statements)}...")
                connection.execute(text(statement.strip()))
                
            print(f"✅ {description} 执行成功！")
            return True
            
    except Exception as e:
        print(f"❌ {description} 执行失败: {e}")
        return False


def create_table() -> bool:
    """创建 app_logs_min 表和相关索引"""
    return execute_ddl_statements(
        ALL_DDL_STATEMENTS,
        "创建 app_logs_min 表和索引"
    )


def rollback_table() -> bool:
    """删除 app_logs_min 表"""
    return execute_ddl_statements(
        ROLLBACK_DDL_STATEMENTS,
        "删除 app_logs_min 表"
    )


def check_table_exists() -> bool:
    """检查 app_logs_min 表是否存在"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return 'app_logs_min' in tables
    except Exception as e:
        print(f"检查表失败: {e}")
        return False


def update_table() -> bool:
    """更新 app_logs_min 表结构"""
    # 使用 DDL 文件中定义的更新语句
    if not UPDATE_DDL_STATEMENTS:
        print("暂无表结构更新")
        return True
    
    return execute_ddl_statements(
        UPDATE_DDL_STATEMENTS,
        "更新 app_logs_min 表结构"
    )


def check_table_status() -> None:
    """检查 app_logs_min 表的状态"""
    print("检查 app_logs_min 表状态:")
    print("-" * 30)
    
    exists = check_table_exists()
    status = "✅ 存在" if exists else "❌ 不存在"
    print(f"app_logs_min         {status}")
    
    if exists:
        # 获取表的列信息
        try:
            inspector = inspect(engine)
            columns = inspector.get_columns('app_logs_min')
            print(f"\n表结构 (共 {len(columns)} 列):")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
        except Exception as e:
            print(f"获取表结构失败: {e}")
    
    print("-" * 30)


def main():
    """主函数 - 解析命令行参数并执行相应操作"""
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="app_logs_min 表迁移脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m db.migrate                    # 创建 app_logs_min 表
  python -m db.migrate --rollback         # 删除 app_logs_min 表
  python -m db.migrate --check            # 检查表状态
  python -m db.migrate --update           # 更新表结构
        """
    )
    
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='删除 app_logs_min 表'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='检查 app_logs_min 表状态'
    )
    
    parser.add_argument(
        '--update',
        action='store_true',
        help='更新 app_logs_min 表结构'
    )
    
    args = parser.parse_args()
    
    # 测试数据库连接
    try:
        with engine.connect() as connection:
            print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)
    
    # 执行相应操作
    if args.check:
        check_table_status()
        return
    
    if args.rollback:
        success = rollback_table()
        if success:
            print("\n回滚完成！")
            check_table_status()
        sys.exit(0 if success else 1)
    
    if args.update:
        success = update_table()
        if success:
            print("\n表结构更新完成！")
            check_table_status()
        else:
            print("\n表结构更新失败！")
        sys.exit(0 if success else 1)
    
    # 默认操作：创建表
    success = create_table()
    
    if success:
        print("\n迁移完成！")
        print("\n当前表状态:")
        check_table_status()
    else:
        print("\n迁移失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()