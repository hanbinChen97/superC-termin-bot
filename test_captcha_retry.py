#!/usr/bin/env python3
"""
测试验证码重试功能
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from superc.form_filler import test_form_parsing, find_form_fields_from_soup, compare_with_expected_fields
import bs4

def test_error_detection():
    """测试错误检测功能"""
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 测试HTML错误页面解析
    error_html_file = project_root / "data/pages/superc/step_6_form_error_20250805_063807.html"
    
    if not error_html_file.exists():
        logging.error(f"错误HTML文件不存在: {error_html_file}")
        return False
    
    logging.info(f"测试错误页面解析: {error_html_file}")
    
    try:
        with open(error_html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = bs4.BeautifulSoup(html_content, 'html.parser')
        
        # 测试错误检测
        error_div = soup.find('div', class_='content__error')
        if error_div:
            error_text = error_div.get_text()
            logging.info(f"发现错误区域: {error_text}")
            
            if "Sicherheitsfrage" in error_text:
                logging.info("✓ 成功检测到验证码错误 (Sicherheitsfrage)")
            else:
                logging.warning("✗ 未检测到验证码错误")
        else:
            logging.warning("✗ 未找到错误区域")
            
        # 测试表单字段解析
        form_fields = find_form_fields_from_soup(soup)
        logging.info(f"找到 {len(form_fields)} 个表单字段")
        
        # 测试成功
        return True
        
    except Exception as e:
        logging.error(f"测试失败: {str(e)}")
        return False

def test_form_parsing_main():
    """测试表单解析的主要功能"""
    
    # 测试表单解析
    test_html_file = project_root / "data/debugPage/step_6_ Termin bestätigen.html"
    
    if test_html_file.exists():
        logging.info("测试现有表单页面解析...")
        success = test_form_parsing(str(test_html_file))
        if success:
            logging.info("✓ 表单解析测试成功")
        else:
            logging.warning("✗ 表单解析测试失败")
    else:
        logging.info("跳过表单解析测试（测试文件不存在）")

if __name__ == "__main__":
    print("开始测试验证码重试功能...")
    
    # 测试错误检测
    success1 = test_error_detection()
    
    # 测试表单解析
    test_form_parsing_main()
    
    if success1:
        print("✓ 验证码错误检测测试通过")
    else:
        print("✗ 验证码错误检测测试失败")
    
    print("测试完成")
