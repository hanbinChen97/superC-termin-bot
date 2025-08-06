"""
Appointment Checker Logic Flow

fold: cmd k + cmd 0
"""
#  python -m superc.appointment_checker


import requests
import bs4
import logging
from typing import Tuple, Union, Optional
from urllib.parse import urljoin

# 使用相对导入
from . import config
from .utils import save_page_content, validate_page_step
from .form_filler import fill_form_with_captcha_retry
from datetime import datetime
import json
from .profile import Profile


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
    纯检查逻辑：仅检查是否有可用预约，不进行选择
    返回: (有预约?, 信息, suggest_response)
    """
    payload = {
        'loc': str(loc),
        'gps_lat': '55.77858',
        'gps_long': '65.07867',
        'select_location': submit_text
    }
    # 进入 Schritt 4
    res = session.post(url, data=payload)
    
    if not validate_page_step(res, "4"):
        return False, "Schritt 4 失败: 页面验证失败，未找到预期的Schritt 4标题" + res.text, None
    
    log_verbose("Schritt 4: 成功进入预约时间检查页面")
    
    # 这不是很清楚。。。
    suggest_url = urljoin(BASE_URL, 'suggest')
    suggest_res = session.get(suggest_url)
    # save_page_content(suggest_res.text, '4_availability', location_name)

    # 检查是否有可用预约时间
    if "Kein freier Termin verfügbar" in suggest_res.text:
        return False, "当前没有可用预约时间", None

    # 这是关键信息，始终输出
    logging.info("Schritt 4: 发现可用预约时间")
    return True, "发现可用预约时间", suggest_res

def select_appointment_and_choose_profile(session: requests.Session, suggest_res: requests.Response, location_name: str, current_profile: Optional[Profile], hanbin_profile: Optional[Profile]) -> Tuple[bool, str, Optional[bs4.BeautifulSoup], Optional[Profile]]:
    """
    选择第一个可用预约并根据日期选择profile
    返回: (成功?, 消息, soup, 选择的profile)
    """
    soup = bs4.BeautifulSoup(suggest_res.text, 'html.parser')
    details_container = soup.find("details", {"id": "details_suggest_times"})
    if not details_container:
        details_container = soup.find("div", {"id": "sugg_accordion"})

    if not details_container:
        return False, "Schritt 4 失败: 在预约页面找不到时间容器", None, None
    
    first_available_form = details_container.find("form", {"class": "suggestion_form"})

    if not first_available_form:
        return False, "Schritt 4 失败: 有可用时间但无法找到具体的预约表单", None, None

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
    
    # 根据日期选择profile
    selected_profile = choose_profile_by_date(date_display, current_profile, hanbin_profile)
    if not selected_profile:
        return False, f"预约时间 {date_display} 无法选择合适的profile", None, None
    
    # 时间来自 <button>
    time_button = first_available_form.find("button", {"type": "submit"})
    time_info = time_button.get('title') if time_button else "未知时间"

    # 这是关键信息，始终输出
    logging.info(f"Schritt 4: 找到可用时间: {date_display} {time_info}, 选择profile: {selected_profile.full_name if selected_profile else '未知'}")
    logging.info("正在提交预约选择...")
    
    submit_url = urljoin(BASE_URL, 'suggest')
    submit_res = session.post(submit_url, data=form_data)
    save_page_content(submit_res.text, '5_term_selected', location_name)

    if not validate_page_step(submit_res, "5"):
        logging.warning("Schritt 4 失败: 提交时间后未进入Schritt 5，可能选择失败")
        return False, "Schritt 4 失败: 提交时间后未进入Schritt 5", None, None

    submit_soup = bs4.BeautifulSoup(submit_res.text, 'html.parser')
    logging.info("Schritt 4 完成: 成功选择时间，进入Schritt 5表单页面")
    return True, "Schritt 4 完成: 成功选择时间，进入Schritt 5表单页面", submit_soup, selected_profile

def choose_profile_by_date(appointment_date_str: str, current_profile: Optional[Profile], hanbin_profile: Optional[Profile]) -> Optional[Profile]:
    """
    根据预约日期选择profile
    规则：月份 < 9 使用 hanbin_profile，>= 9 使用 current_profile
    """
    try:
        # 从 "Mittwoch, 27.08.2025" 中提取月份
        date_part = appointment_date_str.split(', ')[1] 
        day, month, year = date_part.split('.')
        month_int = int(month)

        cutoff_month = 10  # 10月作为分界点

        if month_int < cutoff_month:
            # 使用hanbin_profile
            if hanbin_profile:
                logging.info(f"预约日期为 {appointment_date_str}，月份早于{cutoff_month}月，使用hanbin_profile")
                return hanbin_profile
            else:
                logging.error("无法使用hanbin_profile，因为未设置")
                return None
        else:
            # 使用current_profile
            if current_profile:
                logging.info(f"预约日期为 {appointment_date_str}，月份为{cutoff_month}月或更晚，使用current_profile")
                return current_profile
            else:
                # 如果没有current_profile，回退到hanbin_profile
                if hanbin_profile:
                    logging.info(f"预约日期为 {appointment_date_str}，无current_profile，回退使用hanbin_profile")
                    return hanbin_profile
                else:
                    logging.error("无可用的profile")
                    return None

    except (IndexError, ValueError) as e:
        logging.warning(f"无法从 '{appointment_date_str}' 解析日期，使用current_profile作为默认。错误: {e}")
        return current_profile if current_profile else hanbin_profile

def schritt_4_check_appointment_availability(session: requests.Session, url: str, loc: str, submit_text: str, location_name: str, current_profile: Optional[Profile], hanbin_profile: Optional[Profile]) -> Tuple[bool, str, Optional[bs4.BeautifulSoup], Optional[Profile]]:
    """
    Schritt 4: 检查预约时间可用性并选择第一个可用时间，同时选择合适的profile
    返回: (成功?, 消息, soup, 选择的profile)
    """
    # 第一阶段：仅检查是否有预约
    has_appointment, check_message, suggest_res = check_appointment_availability(session, url, loc, submit_text, location_name)
    
    if not has_appointment:
        return False, check_message, None, None
    
    # 第二阶段：有预约时才进行选择并选择profile
    if suggest_res is None:
        return False, "内部错误：suggest_res为空", None, None
    
    return select_appointment_and_choose_profile(session, suggest_res, location_name, current_profile, hanbin_profile)

def schritt_5_fill_form(session: requests.Session, soup: bs4.BeautifulSoup, location_name: str, selected_profile: Optional[Profile]) -> Tuple[bool, str, Optional[bs4.BeautifulSoup]]:
    """
    Schritt 5: 填写表单 - 使用schritt 4选择的profile，支持验证码重试
    """
    if not selected_profile:
        return False, "Schritt 5 失败: 未提供选择的profile", None

    logging.info(f"Schritt 5: 准备使用 {selected_profile.full_name} profile 填写表单...")
    
    # 使用带重试的表单填写函数
    result = fill_form_with_captcha_retry(session, soup, location_name, selected_profile, max_retries=3)

    # 检查表单填写结果
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

def run_check(location_config: dict, current_profile: Optional[Profile], hanbin_profile: Optional[Profile]) -> Tuple[bool, str]:
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
    success, res_or_error = get_initial_page(session)
    if not success: 
        logging.error(f"获取初始页面失败: {res_or_error}")
        return False, str(res_or_error)
    
    res = res_or_error  # 此时已确认success为True，所以res_or_error是Response对象
    assert isinstance(res, requests.Response)  # 类型断言

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
        return False, str(result)
    loc, res = result

    log_verbose("=== Schritt 4: 检查预约时间可用性并选择 ===")
    # Schritt 4: 检查预约时间可用性并选择第一个，同时选择profile
    success, message, soup, selected_profile = schritt_4_check_appointment_availability(session, url, loc, location_config["submit_text"], location_name, current_profile, hanbin_profile)
    
    if not success:
        logging.info(f"Schritt 4 结果: {message}")
        return False, message

    logging.info("=== Schritt 5: 填写表单 ===")
    # Schritt 5: 填写表单，使用schritt 4选择的profile
    if soup is None or selected_profile is None:
        return False, "内部错误：soup或selected_profile为空"
        
    success, message, updated_soup = schritt_5_fill_form(session, soup, location_name, selected_profile)
    if not success:
        logging.error(f"Schritt 5 失败: {message}")
        return False, message

    logging.info("=== Schritt 6: 邮件确认 ===")
    # Schritt 6: 邮件确认
    final_soup = updated_soup if updated_soup is not None else soup
    result = schritt_6_confirm_booking(session, final_soup, location_name)
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
    
    # 为测试提供 None 的 profile 参数
    success, message = run_check(location_config, None, None)
    print(f"检查结果: {'成功' if success else '失败'} - {message}")
