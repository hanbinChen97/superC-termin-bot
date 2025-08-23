#!/usr/bin/env python3
"""
测试表单解析功能
"""

import logging
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from superc.form_filler import test_form_parsing

def main():
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_form_parsing.log', encoding='utf-8')
        ]
    )
    
    # 测试HTML文件路径
    html_file_path = "/home/hbchen/Projects/superC-termin-bot/data/pages/superc/step_5_term_selected_20250804_085200.html"
    
    logging.info("开始测试表单解析功能")
    
    # 检查文件是否存在
    if not os.path.exists(html_file_path):
        logging.error(f"HTML文件不存在: {html_file_path}")
        return False
    
    # 运行测试
    success = test_form_parsing(html_file_path)
    
    if success:
        logging.info("✅ 表单解析测试成功完成!")
    else:
        logging.error("❌ 表单解析测试失败!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
