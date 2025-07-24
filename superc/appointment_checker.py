# uv run superc/appointment_checker.py


import requests
import bs4
import logging
from typing import Tuple, Union, Optional
from urllib.parse import urljoin

# 使用相对导入
from . import config
from .utils import save_page_content, download_captcha, validate_page_step
from .form_filler import fill_form
from datetime import datetime
import json


USER_AGENT = config.USER_AGENT
BASE_URL = config.BASE_URL


def log_verbose(message: str, level: int = logging.INFO):
    """
    根据配置决定是否输出详细日志
    """
    if config.VERBOSE_LOGGING:
        logging.log(level, message)


def get_initial_page(session: requests.Session) -> Tuple[bool, Union[requests.Response, str]]:
    """
    获取初始页面 - 进入Schritt 2
    """
    url = urljoin(BASE_URL, 'select2?md=1')
    res = session.get(url)
    
    if validate_page_step(res, "2"):
        log_verbose("成功获取初始页面，进入Schritt 2")
        return True, res
    else:
        return False, "页面验证失败，未找到预期的Schritt 2标题"

def schritt_2_select_service_and_location_type(session: requests.Session, res: requests.Response, selection_text: str) -> Tuple[bool, str]:
    """
    Schritt 2: 选择RWTH Studenten服务类型并选择地点类型 (Super C oder Infostelle)
    """
    soup = bs4.BeautifulSoup(res.content, 'html.parser')
    header = soup.find("h3", string=lambda s: selection_text in s if s else False)
    if not header:
        return False, f"无法找到包含 '{selection_text}' 的选项"
    
    next_sibling = header.find_next_sibling()
    if not next_sibling:
        return False, "无法找到预约选项的同级元素"
    
    li_elements = next_sibling.find_all("li")
    if not li_elements:
        return False, "无法找到预约选项列表"
    
    cnc_id = li_elements[0].get("id").split("-")[-1]
    url = urljoin(BASE_URL, f"location?mdt=89&select_cnc=1&cnc-{cnc_id}=1")
    log_verbose(f"Schritt 2 完成: 成功选择服务类型")
    return True, url

def schritt_3_add_location_info(session: requests.Session, url: str) -> Tuple[bool, Union[Tuple[str, requests.Response], str]]:
    """
    Schritt 3: 添加位置信息 (Standortauswahl)
    """
    res = session.get(url)
    
    if not validate_page_step(res, "3"):
        return False, "Schritt 3 失败: 页面验证失败，未找到预期的Schritt 3标题"
    
    soup = bs4.BeautifulSoup(res.content, 'html.parser')
    loc = soup.find('input', {'name': 'loc'})
    if not loc:
        return False, "无法在页面上找到位置信息 'loc'"
    
    log_verbose("Schritt 3 完成: 成功添加位置信息")
    return True, (loc.get('value'), res)

def check_appointment_availability(session: requests.Session, url: str, loc: str, submit_text: str, location_name: str) -> Tuple[bool, str, Optional[requests.Response]]:
    """
    纯检查逻辑：仅检查是否有可用预约，不进行选择和profile设置
    返回: (有预约?, 信息, suggest_response)
    """
    payload = {
        'loc': str(loc),
        'gps_lat': '55.77858',
        'gps_long': '65.07867',
        'select_location': submit_text
    }
    res = session.post(url, data=payload)
    
    if not validate_page_step(res, "4"):
        return False, "Schritt 4 失败: 页面验证失败，未找到预期的Schritt 4标题", None
    
    log_verbose("Schritt 4: 成功进入预约时间检查页面")
    
    # 检查是否有可用预约时间
    suggest_url = urljoin(BASE_URL, 'suggest')
    suggest_res = session.get(suggest_url)
    # save_page_content(suggest_res.text, '4_availability', location_name)

    if "Kein freier Termin verfügbar" in suggest_res.text:
        return False, "Schritt 4 结果: 当前没有可用预约时间", None

    # 这是关键信息，始终输出
    logging.info("Schritt 4: 发现可用预约时间")
    return True, "发现可用预约时间", suggest_res

def get_profile_user_defined(file_path: str) -> Optional[dict]:
    """
    获取用户定义的个人信息文件内容
    用于月份 < 9 的情况
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        return profile_data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"无法读取用户定义文件 {file_path}: {e}")
        return None

def set_profile(appointment_date_str: str, db_profile=None) -> bool:
    """
    根据预约时间设置当前 profile
    返回是否成功设置profile
    """
    try:
        # 从 "Mittwoch, 27.08.2025" 中提取月份
        date_part = appointment_date_str.split(', ')[1] 
        day, month, year = date_part.split('.')
        month_int = int(month)
        
        rules = config.PROFILE_SELECTION_RULES
        
        if month_int < rules["cutoff_month"]:
            # 使用用户定义文件
            user_profile = get_profile_user_defined(rules["user_defined_file"])
            if user_profile:
                config.currentProfile = {
                    "type": "user_defined",
                    "data": user_profile,
                    "source": rules["user_defined_file"]
                }
                logging.info(f"预约日期为 {appointment_date_str}，月份早于{rules['cutoff_month']}月，使用用户定义文件 '{rules['user_defined_file']}'")
                return True
            else:
                logging.error(f"无法加载用户定义文件 {rules['user_defined_file']}")
                return False
        else:
            # 使用数据库中的profile
            if db_profile and rules["use_database"]:
                config.currentProfile = {
                    "type": "database",
                    "data": db_profile,
                    "source": "database"
                }
                logging.info(f"预约日期为 {appointment_date_str}，月份为{rules['cutoff_month']}月或更晚，使用数据库中的用户信息 (ID: {db_profile.id})")
                return True
            else:
                logging.info(f"预约日期为 {appointment_date_str}，月份为{rules['cutoff_month']}月或更晚，但无可用的数据库profile，跳过此预约")
                return False

    except (IndexError, ValueError) as e:
        logging.warning(f"无法从 '{appointment_date_str}' 解析日期，无法设置profile。错误: {e}")
        return False

def select_appointment_and_set_profile(session: requests.Session, suggest_res: requests.Response, location_name: str, db_profile=None) -> Tuple[bool, str, Optional[bs4.BeautifulSoup]]:
    """
    选择第一个可用预约并设置profile
    """
    soup = bs4.BeautifulSoup(suggest_res.text, 'html.parser')
    details_container = soup.find("details", {"id": "details_suggest_times"})
    if not details_container:
        details_container = soup.find("div", {"id": "sugg_accordion"})

    if not details_container:
        return False, "Schritt 4 失败: 在预约页面找不到时间容器", None
    
    first_available_form = details_container.find("form", {"class": "suggestion_form"})

    if not first_available_form:
        return False, "Schritt 4 失败: 有可用时间但无法找到具体的预约表单", None

    # 从表单的隐藏字段中提取所有需要提交的数据
    form_data = {inp.get('name'): inp.get('value') for inp in first_available_form.find_all("input", {"type": "hidden"})}
    
    # 提取可读的日期和时间
    date_display = ""
    summary_tag = details_container.find("summary")
    if summary_tag:
        date_display = summary_tag.text.strip()

    # 如果 summary 中没有日期，可以尝试从 form_data 中获取
    if not date_display:
        date_display = form_data.get("date", "未知日期")

    # 设置profile - 这是关键步骤
    if not set_profile(date_display, db_profile):
        return False, f"预约时间 {date_display} 无法设置合适的profile", None
    
    # 时间来自 <button>
    time_button = first_available_form.find("button", {"type": "submit"})
    time_info = time_button.get('title') if time_button else "未知时间"

    # 这是关键信息，始终输出
    logging.info(f"Schritt 4: 找到可用时间: {date_display} {time_info}, 正在提交...")
    
    submit_url = urljoin(BASE_URL, 'suggest')
    submit_res = session.post(submit_url, data=form_data)
    save_page_content(submit_res.text, '5_term_selected', location_name)

    if not validate_page_step(submit_res, "5"):
        logging.warning("Schritt 4 失败: 提交时间后未进入Schritt 5，可能选择失败")
        return False, "Schritt 4 失败: 提交时间后未进入Schritt 5", None

    submit_soup = bs4.BeautifulSoup(submit_res.text, 'html.parser')
    logging.info("Schritt 4 完成: 成功选择时间，进入Schritt 5表单页面")
    return True, "Schritt 4 完成: 成功选择时间，进入Schritt 5表单页面", submit_soup

def schritt_4_check_appointment_availability(session: requests.Session, url: str, loc: str, submit_text: str, location_name: str, db_profile=None) -> Tuple[bool, str, Optional[bs4.BeautifulSoup]]:
    """
    Schritt 4: 重构后的主函数，调用上述两个新函数
    """
    # 第一阶段：仅检查是否有预约
    has_appointment, check_message, suggest_res = check_appointment_availability(session, url, loc, submit_text, location_name)
    
    if not has_appointment:
        return False, check_message, None
    
    # 第二阶段：有预约时才进行选择和profile设置
    return select_appointment_and_set_profile(session, suggest_res, location_name, db_profile)

def schritt_5_fill_form(session: requests.Session, soup: bs4.BeautifulSoup, location_name: str) -> Tuple[bool, str, Optional[bs4.BeautifulSoup]]:
    """
    Schritt 5: 填写表单 - 使用 currentProfile 而不是固定文件
    """
    if not config.currentProfile:
        return False, "Schritt 5 失败: 未设置currentProfile", None
    
    success, captcha_path = download_captcha(session, soup, location_name)

    if not success:
        return False, f"Schritt 5 失败: {captcha_path}", None

    logging.info(f"Schritt 5: 准备使用 {config.currentProfile['type']} profile 填写表单...")
    result = fill_form(session, soup, captcha_path, location_name)
    if result[0]:
        # 这是关键信息，始终输出
        logging.info("Schritt 5 完成: 表单填写成功，进入Schritt 6")
        # 返回新的soup供 Schritt 6 使用
        return True, "Schritt 5 完成: 表单填写成功", soup  # 这里可能需要更新为新的response soup
    else:
        return False, f"Schritt 5 失败: {result[1]}", None

def schritt_6_confirm_booking(session: requests.Session, soup: bs4.BeautifulSoup, location_name: str) -> Tuple[bool, str]:
    """
    Schritt 6: 邮件确认 - 完成预约确认流程
    """
    # 这里可能需要处理邮件确认步骤
    # 目前假设 fill_form 已经完成了所有必要的提交
    # 这是关键信息，始终输出
    logging.info("Schritt 6: 预约已完成，等待邮件确认")
    return True, "Schritt 6 完成: 预约已完成，等待邮件确认"

def run_check(location_config: dict) -> Tuple[bool, str]:
    """
    执行一次完整的预约检查流程 - 6个Schritt步骤
    """
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    location_name = location_config["name"]
    
    # 这是关键信息，始终输出
    # logging.info(f"开始检查 {location_name} 的预约...")
    log_verbose("=== 获取初始页面 ===")

    # 获取初始页面，进入Schritt 2
    success, res = get_initial_page(session)
    if not success: 
        logging.error(f"获取初始页面失败: {res}")
        return False, res

    log_verbose("=== Schritt 2: 选择RWTH服务类型并选择地点类型 ===")
    # Schritt 2: 选择服务类型并选择地点类型
    success, url = schritt_2_select_service_and_location_type(session, res, location_config["selection_text"])
    if not success: 
        logging.error(f"Schritt 2 失败: {url}")
        return False, url

    log_verbose("=== Schritt 3: 添加位置信息 (Standortauswahl) ===")
    # Schritt 3: 添加位置信息
    success, result = schritt_3_add_location_info(session, url)
    if not success: 
        logging.error(f"Schritt 3 失败: {result}")
        return False, result
    loc, res = result

    log_verbose("=== Schritt 4: 检查预约时间可用性并选择 ===")
    # Schritt 4: 检查预约时间可用性并选择第一个
    # 获取数据库profile参数（如果提供了的话）
    db_profile = location_config.get("db_profile", None)
    success, message, soup = schritt_4_check_appointment_availability(session, url, loc, location_config["submit_text"], location_name, db_profile)
    if not success:
        logging.info(f"Schritt 4 结果: {message}")
        return False, message

    logging.info("=== Schritt 5: 填写表单 ===")
    # Schritt 5: 填写表单
    success, message, updated_soup = schritt_5_fill_form(session, soup, location_name)
    if not success:
        logging.error(f"Schritt 5 失败: {message}")
        return False, message

    logging.info("=== Schritt 6: 邮件确认 ===")
    # Schritt 6: 邮件确认
    result = schritt_6_confirm_booking(session, updated_soup or soup, location_name)
    if result[0]:
        # 这是关键信息，始终输出
        logging.info(f"预约成功完成: {result[1]}")
    else:
        logging.error(f"Schritt 6 失败: {result[1]}")
    
    return result

if __name__ == "__main__":
    # 配置日志记录
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # 输出到控制台
        ]
    )
    
    location_config = {
        "name": "superc",
        "selection_text": "Super C",
        "submit_text": "Ausländeramt Aachen - Außenstelle RWTH auswählen"
    }
    
    success, message = run_check(location_config)
    print(f"检查结果: {'成功' if success else '失败'} - {message}")