"""
注意字段的 type。

生日信息 数字。

优化代码：
找到表单中的所有输入字段，输出 log，我要知道找了哪些字段。
并根据字段名称，类型填充相应的值。

目前我对 submit 不是很清楚。

"""

import json
import logging
from urllib.parse import urljoin
from typing import Optional, Tuple, Dict, Any, List, Union
import httpx
import bs4
from bs4 import BeautifulSoup, Tag

from .gpt_call import recognize_captcha_with_gpt
from .utils import save_page_content, download_captcha
from .config import USER_AGENT, BASE_URL
from . import config
from .profile import Profile


def find_form_fields_from_soup(soup: BeautifulSoup) -> Dict[str, Dict[str, Any]]:
    """
    从soup中智能分析表单字段，返回字段信息字典
    
    Args:
        soup: BeautifulSoup对象
        
    Returns:
        Dict: 字段信息字典，格式为 {field_name: {type, required, element, ...}}
    """
    logging.info("\n开始分析表单字段...")
    
    form = soup.find('form')
    if not form or not isinstance(form, Tag):
        logging.error("未找到表单")
        return {}
    
    form_fields = {}
    
    # 查找所有输入字段
    all_inputs = form.find_all(['input', 'textarea', 'select'])
    
    for element in all_inputs:
        if not isinstance(element, Tag):
            continue
            
        field_name = element.get('name')
        if not field_name:
            continue
            
        field_info = {
            'element': element,
            'type': element.get('type', 'text') if element.name == 'input' else element.name,
            'required': False,
            'id': element.get('id', ''),
            'value': element.get('value', ''),
            'max_length': element.get('maxlength', ''),
            'placeholder': element.get('placeholder', ''),
            'title': element.get('title', ''),
        }
        
        # 检查是否为必填字段 (多种方式)
        # 1. required属性
        if element.get('required') == 'required':
            field_info['required'] = True
            
        # 2. required类
        classes = element.get('class')
        if classes:
            if isinstance(classes, list) and 'required' in classes:
                field_info['required'] = True
            elif isinstance(classes, str) and 'required' in classes:
                field_info['required'] = True
            
        # 3. 查找对应的label是否有pflicht类
        label = None
        if field_info['id']:
            label = form.find('label', {'for': field_info['id']})
        if label and isinstance(label, Tag):
            label_classes = label.get('class')
            if label_classes and 'pflicht' in str(label_classes):
                field_info['required'] = True
            
        # 记录字段信息
        form_fields[field_name] = field_info
        
        # logging.info(f"  找到字段: {field_name}")
        # logging.info(f"    类型: {field_info['type']}")
        # logging.info(f"    必填: {field_info['required']}")
        # logging.info(f"    ID: {field_info['id']}")
        # logging.info(f"    标题: {field_info['title']}")
    
    logging.info(f"\n总共找到 {len(form_fields)} 个字段")
    return form_fields


def compare_with_expected_fields(found_fields: Dict[str, Dict[str, Any]], expected_fields: Dict[str, str]) -> None:
    """
    对比发现的字段和预期字段，记录差异
    
    Args:
        found_fields: 从表单中发现的字段
        expected_fields: 预期的字段字典 (key: 字段名, value: 示例值)
    """
    logging.info("\n开始对比字段...")
    
    found_field_names = set(found_fields.keys())
    expected_field_names = set(expected_fields.keys())
    
    # 找到匹配的字段
    matching_fields = found_field_names & expected_field_names
    logging.info(f"匹配的字段 ({len(matching_fields)}): {sorted(matching_fields)}")
    
    # 找到缺失的字段 (预期有但实际没找到)
    missing_fields = expected_field_names - found_field_names
    if missing_fields:
        logging.warning(f"缺失的字段 ({len(missing_fields)}): {sorted(missing_fields)}")
        for field in missing_fields:
            logging.warning(f"  预期字段 '{field}' 未在表单中找到")
    
    # 找到额外的字段 (实际找到但不在预期中)
    extra_fields = found_field_names - expected_field_names
    if extra_fields:
        logging.info(f"额外的字段 ({len(extra_fields)}): {sorted(extra_fields)}")
        for field in extra_fields:
            field_info = found_fields[field]
            logging.info(f"  额外字段 '{field}' - 类型: {field_info['type']}, 必填: {field_info['required']}")
    
    # 详细分析匹配字段的属性
    logging.info(f"\n匹配字段详细信息:")
    for field in sorted(matching_fields):
        field_info = found_fields[field]
        logging.info(f"  {field}:")
        logging.info(f"    类型: {field_info['type']}")
        logging.info(f"    必填: {field_info['required']}")
        logging.info(f"    ID: {field_info['id']}")
        logging.info(f"    预期值示例: {expected_fields[field]}")
    
    # 总结
    total_expected = len(expected_field_names)
    total_found = len(found_field_names)
    match_rate = len(matching_fields) / total_expected * 100 if total_expected > 0 else 0
    
    logging.info(f"\n对比总结:")
    logging.info(f"  预期字段数: {total_expected}")
    logging.info(f"  实际找到字段数: {total_found}")
    logging.info(f"  匹配字段数: {len(matching_fields)}")
    logging.info(f"  匹配率: {match_rate:.1f}%")
    
    if missing_fields:
        logging.warning(f"  缺失字段数: {len(missing_fields)}")
    if extra_fields:
        logging.info(f"  额外字段数: {len(extra_fields)}")


def test_form_parsing(html_file_path: str) -> bool:
    """
    测试表单解析功能
    
    Args:
        html_file_path: HTML文件路径
        
    Returns:
        bool: 测试是否成功
    """
    logging.info(f"\n开始测试表单解析: {html_file_path}")
    
    # 预期的表单字段 (基于测试结果更新字段名)
    expected_fields = {
        'vorname': 'zijie',
        'nachname': 'zhou', 
        'email': 'zhouzijie86@gmail.com',
        'phone': '017660936757',
        # 更新为实际HTML中的字段名
        'geburtsdatumDay': '27',
        'geburtsdatumMonth': '8', 
        'geburtsdatumYear': '2001',
        'emailCheck': 'zhouzijie86@gmail.com',
        'comment': '',
        'captcha_code': 'CiRWg',
        'agreementChecked': 'on',
        'hunangskrukka': '',
        'submit': 'Reservieren'
    }
    
    try:
        # 读取HTML文件
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 解析HTML
        soup = bs4.BeautifulSoup(html_content, 'html.parser')
        
        # 分析表单字段
        found_fields = find_form_fields_from_soup(soup)
        
        if not found_fields:
            logging.error("未找到任何表单字段")
            return False
        
        # 对比字段
        compare_with_expected_fields(found_fields, expected_fields)
        
        # 检查关键字段映射
        logging.info(f"\n检查关键字段映射:")
        
        # 检查生日字段的实际名称
        birthday_fields = {k: v for k, v in found_fields.items() if 'geburtsdatum' in k.lower()}
        logging.info(f"生日相关字段: {list(birthday_fields.keys())}")
        
        # 检查邮箱确认字段的实际名称  
        email_fields = {k: v for k, v in found_fields.items() if 'email' in k.lower()}
        logging.info(f"邮箱相关字段: {list(email_fields.keys())}")
        
        # 检查验证码字段的实际名称
        captcha_fields = {k: v for k, v in found_fields.items() if 'captcha' in k.lower()}
        logging.info(f"验证码相关字段: {list(captcha_fields.keys())}")
        
        return True
        
    except Exception as e:
        logging.error(f"测试表单解析失败: {str(e)}")
        return False


def map_profile_to_form_data(profile: Profile, form_fields: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    智能映射Profile数据到表单字段
    
    Args:
        profile: Profile对象
        form_fields: 表单字段信息字典
        
    Returns:
        Dict: 映射后的表单数据
    """
    logging.info("\n开始映射Profile数据到表单字段...")
    
    if not profile:
        logging.error("Profile对象为空")
        return {}
    
    # 获取Profile的原始数据
    profile_data = profile.to_form_data()
    
    # 字段映射规则 - 处理命名不一致的情况
    field_mapping = {
        # Profile字段名 -> 表单字段名的映射
        'vorname': ['vorname'],
        'nachname': ['nachname'], 
        'email': ['email'],
        'phone': ['phone', 'tel', 'telefon', 'telefonnummer'],
        # 根据测试结果更新生日字段映射：实际使用驼峰命名
        'geburtsdatum_day': ['geburtsdatumDay', 'birthday_day'],
        'geburtsdatum_month': ['geburtsdatumMonth', 'birthday_month'],
        'geburtsdatum_year': ['geburtsdatumYear', 'birthday_year'],
    }
    
    # 特殊字段映射
    special_mappings = {
        'emailCheck': 'email',  # 邮箱确认字段映射到邮箱
        'emailwhlg': 'email',   # 邮箱重复字段 (根据HTML ID)
        'email_confirmation': 'email',
        'email_repeat': 'email',
    }
    
    form_data = {}
    
    # 1. 先处理直接映射
    for profile_field, form_field_names in field_mapping.items():
        profile_value = profile_data.get(profile_field)
        
        if profile_value is not None:
            # 查找匹配的表单字段
            for form_field_name in form_field_names:
                if form_field_name in form_fields:
                    # 根据字段类型进行适当转换
                    field_info = form_fields[form_field_name]
                    
                    if field_info['type'] == 'number':
                        # 数字类型字段
                        try:
                            form_data[form_field_name] = int(profile_value)
                        except (ValueError, TypeError):
                            form_data[form_field_name] = profile_value
                    else:
                        # 文本类型字段
                        form_data[form_field_name] = str(profile_value)
                    
                    logging.info(f"  映射: {profile_field} -> {form_field_name} = '{form_data[form_field_name]}'")
                    break
    
    # 2. 处理特殊映射 (如邮箱确认)
    for form_field_name, profile_field in special_mappings.items():
        if form_field_name in form_fields and profile_field in profile_data:
            form_data[form_field_name] = profile_data[profile_field]
            logging.info(f"  特殊映射: {profile_field} -> {form_field_name} = '{form_data[form_field_name]}'")
    
    # 3. 设置固定字段
    fixed_fields = {
        'comment': '',  # 备注通常为空
        'hunangskrukka': '',  # 蜜罐字段必须为空
        'agreementChecked': 'on',  # 同意条款
        'submit': 'Reservieren',  # 提交按钮值
    }
    
    for field_name, value in fixed_fields.items():
        if field_name in form_fields:
            form_data[field_name] = value
            logging.info(f"  固定字段: {field_name} = '{value}'")
    
    # 4. 检查未映射的必填字段
    unmapped_required = []
    for field_name, field_info in form_fields.items():
        if field_info['required'] and field_name not in form_data:
            # 跳过验证码等特殊字段
            if field_name not in ['captcha_code', 'captcha_result']:
                unmapped_required.append(field_name)
    
    if unmapped_required:
        logging.warning(f"  发现未映射的必填字段: {unmapped_required}")
    
    logging.info(f"\n成功映射 {len(form_data)} 个字段")
    return form_data


def check_captcha_error_from_response(response_text: str) -> bool:
    """
    通过DOM检查响应中是否包含验证码错误
    
    Args:
        response_text: HTTP响应文本
        
    Returns:
        bool: 是否为验证码错误
    """
    try:
        soup_response = bs4.BeautifulSoup(response_text, 'html.parser')
        error_div = soup_response.find('div', class_='content__error')
        
        if error_div:
            error_text = error_div.get_text()
            logging.info(f"检测到错误区域内容: {error_text}")
            
            # 检查是否包含"Sicherheitsfrage"
            if "Sicherheitsfrage" in error_text:
                logging.error("通过DOM检测到验证码错误 (Sicherheitsfrage)")
                return True
        
        return False
        
    except Exception as e:
        logging.error(f"检查验证码错误时发生异常: {str(e)}")
        return False


def fill_form_with_captcha_retry(session: httpx.Client, soup: bs4.BeautifulSoup, location_name: str, profile: Profile, max_retries: int = 3) -> Tuple[bool, str]:
    """
    填写表单并提交，支持验证码重试
    :param session: httpx.Client 对象
    :param soup: BeautifulSoup 对象
    :param location_name: 地点名称，用于保存文件
    :param profile: Profile 对象，必需参数
    :param max_retries: 验证码最大重试次数，默认3次
    :return: (是否成功, 响应信息)
    """
    
    for attempt in range(max_retries):
        is_retry = attempt > 0
        attempt_info = f"(第{attempt + 1}次尝试)" if is_retry else ""
        
        if is_retry:
            logging.info(f"验证码重试 {attempt_info}")
        else:
            logging.info("开始填写表单...")
        
        # 执行表单填写
        success, message, response_text = fill_form(session, soup, location_name, profile)
        
        if success:
            return True, message
        
        if "zu vieler Terminanfragen" in message:
            # 直接返回，不重试
            return False, message

        is_captcha_error = "验证码错误" in message
        
        if not is_captcha_error:
            # 非验证码错误，直接返回失败
            logging.info("检测到非验证码错误，不进行重试")
            return False, message
        
        # 验证码错误，准备重试
        if attempt < max_retries - 1:
            logging.warning(f"验证码错误 {attempt_info}，准备重试...")
        else:
            # 已达到最大重试次数
            logging.error(f"验证码重试失败，已达到最大重试次数({max_retries})")
            return False, f"验证码重试失败: {message}"
    
    return False, "未知错误"


def fill_form(session: httpx.Client, soup: bs4.BeautifulSoup, location_name: str, profile: Profile) -> Tuple[bool, str, Optional[str]]:
    """
    填写表单并提交
    :param session: httpx.Client 对象
    :param soup: BeautifulSoup 对象
    :param location_name: 地点名称，用于保存文件
    :param profile: Profile 对象，必需参数
    :return: (是否成功, 响应信息, 响应文本)
    """
    logging.info("\n开始智能填写表单...")
    
    # 直接使用 Profile 对象的 to_form_data() 方法并映射字段名
    if not profile:
        logging.error("profile 参数未提供")
        return False, "profile 参数未提供", None
    
    try:
        # 1. 智能分析表单字段
        form_fields = find_form_fields_from_soup(soup)
        if not form_fields:
            return False, "未找到有效的表单字段", None
        
        # 2. 智能映射Profile数据到表单
        form_data = map_profile_to_form_data(profile, form_fields)
        if not form_data:
            return False, "Profile数据映射失败", None
        
        # 记录映射结果
        logging.info(f"智能映射完成，生成 {len(form_data)} 个字段")
            
    except Exception as e:
        logging.error(f"智能表单分析失败: {str(e)}")
        # 如果智能分析失败，回退到传统方法
        logging.info("回退到传统表单填写方法...")
        try:
            form_data_raw = profile.to_form_data()
            
            # 映射为页面表单需要的字段名（驼峰命名）
            personal_info = {
                "vorname": form_data_raw.get("vorname", ""),
                "nachname": form_data_raw.get("nachname", ""),
                "email": form_data_raw.get("email", ""),
                "phone": form_data_raw.get("phone", ""),
                # 映射为页面表单需要的字段名（驼峰命名）
                "geburtsdatumDay": int(form_data_raw.get("geburtsdatum_day", "1")),  # 数字
                "geburtsdatumMonth": int(form_data_raw.get("geburtsdatum_month", "1")),  # 数字
                "geburtsdatumYear": int(form_data_raw.get("geburtsdatum_year", "1990")),  # 数字
            }
            form_data = personal_info
        except Exception as e2:
            logging.error(f"传统方法也失败: {str(e2)}")
            return False, f"表单数据准备失败: {str(e2)}", None
    
    logging.info(f"表单数据准备完成: {form_data}")

    # 下载并识别验证码
    success, captcha_path = download_captcha(session, soup, location_name)
    if not success:
        return False, f"验证码下载失败: {captcha_path}", None

    logging.info(f"\n开始识别验证码: {captcha_path}")
    captcha_text = recognize_captcha_with_gpt(captcha_path)
    logging.info(f"验证码识别结果: {captcha_text}")
    if not captcha_text:
        logging.error("验证码识别失败")
        return False, "验证码识别失败", None

    # 添加验证码和其他必要字段 
    if 'captcha_code' not in form_data:
        form_data['captcha_code'] = captcha_text
    if 'emailCheck' not in form_data and 'email' in form_data:
        form_data['emailCheck'] = form_data['email']
    if 'comment' not in form_data:
        form_data['comment'] = ''
    if 'agreementChecked' not in form_data:
        form_data['agreementChecked'] = 'on'
    if 'hunangskrukka' not in form_data:
        form_data['hunangskrukka'] = ''  # 蜜罐字段，必须保持为空
    if 'submit' not in form_data:
        form_data['submit'] = 'Reservieren'
    
    # 确保所有生日字段都是数字
    for field in ['geburtsdatumDay', 'geburtsdatumMonth', 'geburtsdatumYear']:
        if field in form_data:
            form_data[field] = int(form_data[field])

    # 记录关键字段的值
    logging.info(f"\n关键字段检查:")
    logging.info(f"  captcha_code (验证码): '{form_data.get('captcha_code')}'")
    logging.info(f"  hunangskrukka (蜜罐字段): '{form_data.get('hunangskrukka')}'")
    logging.info(f"  email: '{form_data.get('email')}'")
    logging.info(f"  emailCheck: '{form_data.get('emailCheck')}'")
    logging.info(f"准备提交的完整表单数据: {form_data}")

    # 获取表单提交URL
    form = soup.find('form')
    if not form or not isinstance(form, Tag):
        logging.error("无法找到表单")
        return False, "无法找到表单", None

    # 收集隐藏字段
    hidden_fields = {}
    for hidden_input in form.find_all('input', type='hidden'):
        if not isinstance(hidden_input, Tag):
            continue
        field_name = hidden_input.get('name')
        field_value = hidden_input.get('value', '')
        if field_name:
            hidden_fields[field_name] = field_value
            logging.info(f"  隐藏字段: {field_name} = '{field_value}'")
    
    form_data.update(hidden_fields)

    # 验证关键字段
    validation_errors = []
    required_fields = ['vorname', 'nachname', 'email', 'phone', 'geburtsdatumYear']
    for field in required_fields:
        if not form_data.get(field):
            validation_errors.append(f"缺少必填字段: {field}")
    
    # 检查邮箱一致性
    if form_data.get('email') != form_data.get('emailCheck'):
        validation_errors.append("邮箱和邮箱确认不一致")
    
    # 确保蜜罐字段为空
    if form_data.get('hunangskrukka') != '':
        logging.warning("警告: hunangskrukka 字段不为空，可能触发反机器人检测")
        form_data['hunangskrukka'] = ''  # 强制设为空
    
    if validation_errors:
        error_msg = "; ".join(validation_errors)
        logging.error(f"表单验证失败: {error_msg}")
        return False, f"表单验证失败: {error_msg}", None

    logging.info(f"\n最终提交的表单数据: {form_data}")

    # 这我不是很清楚
    submit_url = urljoin('https://termine.staedteregion-aachen.de/auslaenderamt/', str(form.get('action', '')))
    logging.info(f"\n提交URL: {submit_url}")


    # ===================================================
    # 提交表单
    # ===================================================
    try:
        headers = {
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://termine.staedteregion-aachen.de/auslaenderamt/'
        }
        logging.info(f"\n准备提交请求，headers: {headers}")

        res = session.post(submit_url, data=form_data, headers=headers)
        
        save_page_content(res.text, '6_form_submitted', location_name)
        logging.info(f"\n表单提交响应状态码: {res.status_code}")

        # 详细分析响应内容
        response_text = res.text
        
        # 检查成功标志
        if "Online-Terminanfrage erfolgreich" in response_text:
            logging.info("预约成功！")
            return True, "预约成功！", response_text
        
        if "zu vieler Terminanfragen" in response_text:
            logging.error("预约失败: zu vieler Terminanfragen")
            save_page_content(response_text, '6_form_error', location_name)
            return False, "预约失败: zu vieler Terminanfragen", response_text

        
        # 通过 DOM 解析，更精确地检测验证码错误
        soup_response = bs4.BeautifulSoup(response_text, 'html.parser')
        error_message = None

        error_div = soup_response.find('div', class_='content__error')
        if error_div:
            error_text = error_div.get_text()
            logging.info(f"检测到错误区域内容: {error_text}")

            # 检查是否包含"Sicherheitsfrage"
            if "Sicherheitsfrage" in error_text:
                error_message = "验证码错误"
                logging.error("检测到验证码错误 (Sicherheitsfrage)")

        if error_message:
            logging.error(f"表单提交失败: {error_message}")
            save_page_content(response_text, '6_form_error', location_name)
            return False, error_message, response_text

        error_message = "未知错误"
        logging.error(f"表单提交失败: {error_message}")
        logging.error(f"响应内容前500字符: {response_text[:500]}...")
        save_page_content(response_text, '6_form_unknown_error', location_name)
        return False, error_message, response_text

    except Exception as e:
        error_msg = f"提交表单时发生异常: {str(e)}"
        logging.error(error_msg)
        return False, error_msg, None
