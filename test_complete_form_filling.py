#!/usr/bin/env python3
"""
测试完整的智能表单填写功能
"""

import logging
import sys
import os
from bs4 import BeautifulSoup

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from superc.form_filler import find_form_fields_from_soup, map_profile_to_form_data
from superc.profile import Profile

def test_complete_form_filling():
    """测试完整的智能表单填写流程"""
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info("开始测试完整的智能表单填写功能")
    
    # 1. 读取HTML文件
    html_file_path = "/home/hbchen/Projects/superC-termin-bot/data/pages/superc/step_5_term_selected_20250804_085200.html"
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        logging.error(f"读取HTML文件失败: {str(e)}")
        return False
    
    # 2. 解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 3. 分析表单字段
    logging.info("\n=== 步骤1: 分析表单字段 ===")
    form_fields = find_form_fields_from_soup(soup)
    
    if not form_fields:
        logging.error("未找到表单字段")
        return False
    
    logging.info(f"成功发现 {len(form_fields)} 个表单字段")
    
    # 4. 创建测试用户Profile
    logging.info("\n=== 步骤2: 创建测试用户Profile ===")
    
    # 直接创建Profile实例
    profile = Profile(
        vorname='zijie',
        nachname='zhou',
        email='zhouzijie86@gmail.com',
        phone='017660936757',
        geburtsdatum_day=27,
        geburtsdatum_month=8,
        geburtsdatum_year=2001,
        preferred_locations='superc'
    )
    
    logging.info(f"创建测试用户: {profile.full_name}, {profile.email}")
    
    # 5. 智能映射Profile到表单数据
    logging.info("\n=== 步骤3: 智能映射Profile到表单数据 ===")
    
    form_data = map_profile_to_form_data(profile, form_fields)
    
    if not form_data:
        logging.error("表单数据映射失败")
        return False
    
    # 6. 验证映射结果
    logging.info("\n=== 步骤4: 验证映射结果 ===")
    
    expected_mappings = {
        'vorname': 'zijie',
        'nachname': 'zhou',
        'email': 'zhouzijie86@gmail.com',
        'phone': 17660936757,  # 数字类型
        'geburtsdatumDay': 27,  # 数字类型
        'geburtsdatumMonth': 8,  # 数字类型
        'geburtsdatumYear': 2001,  # 数字类型
        'emailCheck': 'zhouzijie86@gmail.com',
        'comment': '',
        'hunangskrukka': '',
        'agreementChecked': 'on',
        'submit': 'Reservieren'
    }
    
    success = True
    for field, expected_value in expected_mappings.items():
        actual_value = form_data.get(field)
        
        if actual_value == expected_value:
            logging.info(f"✅ {field}: {actual_value} (符合预期)")
        else:
            logging.error(f"❌ {field}: 期望 '{expected_value}', 实际 '{actual_value}'")
            success = False
    
    # 7. 检查必填字段
    logging.info("\n=== 步骤5: 检查必填字段 ===")
    
    required_fields_check = []
    for field_name, field_info in form_fields.items():
        if field_info['required']:
            if field_name in form_data and form_data[field_name] not in ['', None]:
                logging.info(f"✅ 必填字段 {field_name}: '{form_data[field_name]}'")
            elif field_name in ['captcha_code', 'captcha_result']:
                logging.info(f"⏳ 验证码字段 {field_name}: 需要运行时填写")
            else:
                logging.warning(f"⚠️  必填字段 {field_name}: 未填写或为空")
                required_fields_check.append(field_name)
    
    if required_fields_check:
        logging.warning(f"发现 {len(required_fields_check)} 个未填写的必填字段: {required_fields_check}")
    
    # 8. 总结
    logging.info("\n=== 测试总结 ===")
    logging.info(f"表单字段发现: ✅ {len(form_fields)} 个字段")
    logging.info(f"数据映射: {'✅ 成功' if success else '❌ 失败'}")
    logging.info(f"生成字段数: {len(form_data)} 个")
    logging.info(f"必填字段覆盖: {len([f for f in form_fields if form_fields[f]['required'] and f in form_data])} / {len([f for f in form_fields if form_fields[f]['required']])} 个")
    
    final_success = success and len(form_data) > 10
    
    if final_success:
        logging.info("🎉 智能表单填写功能测试通过！")
    else:
        logging.error("💥 智能表单填写功能测试失败！")
    
    return final_success

if __name__ == "__main__":
    success = test_complete_form_filling()
    sys.exit(0 if success else 1)
