"""
This module contains functions for navigating through the appointment booking pages.
"""

import httpx
import bs4
import logging
from typing import Tuple, Union, Optional
from urllib.parse import urljoin
from datetime import date, datetime
import re

from .. import config
from .utils import validate_page_step, save_page_content
from ..profile import Profile
from .appointment_selector import select_first_appointment
from .form_filler import fill_form_with_captcha_retry


SCHRITT_2_LOGGER = logging.getLogger("schritt2")
SCHRITT_3_LOGGER = logging.getLogger("schritt3")
SCHRITT_4_LOGGER = logging.getLogger("schritt4")
SCHRITT_5_LOGGER = logging.getLogger("schritt5")
SCHRITT_6_LOGGER = logging.getLogger("schritt6")


BASE_URL = config.BASE_URL
USER_AGENT = config.USER_AGENT


def log_verbose(logger: logging.Logger, message: str, level: int = logging.INFO):
    """
    根据配置决定是否输出详细日志
    """
    if config.VERBOSE_LOGGING:
        logger.log(level, message)

def enter_schritt_2_page(session: httpx.Client, selection_text: str) -> Tuple[bool, str]:
    """
    进入Schritt 2页面并完成操作: 选择RWTH Studenten服务类型并选择地点类型 (Super C oder Infostelle)
    """
    url = urljoin(BASE_URL, 'select2?md=1')
    res = session.get(url)
    
    if not validate_page_step(res, "2"):
        return False, "页面验证失败，未找到预期的Schritt 2标题"
    
    log_verbose(SCHRITT_2_LOGGER, "成功进入Schritt 2页面")
    
    # 在页面上进行操作：选择服务类型和地点类型
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
    next_url = urljoin(BASE_URL, f"location?mdt=89&select_cnc=1&cnc-{cnc_id}=1")
    
    return True, next_url

def enter_schritt_3_page(session: httpx.Client, url: str) -> Tuple[bool, Union[str, str]]:
    """
    进入Schritt 3页面并完成操作: 添加位置信息 (Standortauswahl)
    """
    res = session.get(url)
    
    if not validate_page_step(res, "3"):
        return False, "Schritt 3 失败: 页面验证失败，未找到预期的Schritt 3标题"
    
    log_verbose(SCHRITT_3_LOGGER, "成功进入Schritt 3页面")
    
    # 在页面上进行操作：提取位置信息
    soup = bs4.BeautifulSoup(res.content, 'html.parser')
    loc = soup.find('input', {'name': 'loc'})
    if not loc:
        return False, "无法在页面上找到位置信息 'loc'"
    
    log_verbose(SCHRITT_3_LOGGER, "Schritt 3 完成: 成功提取位置信息")
    return True, loc.get('value')

def enter_schritt_4_page(session: httpx.Client, url: str, loc: str, submit_text: str, location_name: str, current_profile: Optional[Profile]) -> Tuple[bool, str, Optional[dict], Optional[Profile], Optional[datetime]]:
    """
    进入Schritt 4页面并完成操作: 检查预约时间可用性并选择第一个可用时间，同时选择合适的profile
    返回: (成功?, 消息, form_data, 选择的profile, 预约日期时间对象)
    """
    payload = {
        'loc': str(loc),
        'gps_lat': '55.77858',
        'gps_long': '65.07867',
        'select_location': submit_text
    }
    # 进入 Schritt 4
    try:
        res = session.post(url, data=payload, follow_redirects=True)
        
        if res.status_code != 200:
            return False, f"Schritt 4 请求失败，状态码: {res.status_code}", None, None, None
            
    except Exception as e:
        return False, f"Schritt 4 请求发生异常: {str(e)}", None, None, None
    
    if not validate_page_step(res, "4"):
        # 检查页面内容，看看实际包含什么
        soup = bs4.BeautifulSoup(res.content, 'html.parser')
        h1_element = soup.find('h1')
        h1_text = h1_element.get_text() if h1_element else "未找到h1元素"
        
        log_verbose(SCHRITT_4_LOGGER, f"页面实际h1内容: {h1_text}")
        
        # 检查是否直接跳转到了suggest页面或其他步骤
        if res.url.path.endswith('/suggest') or "suggest" in str(res.url):
            log_verbose(SCHRITT_4_LOGGER, "检测到已经跳转到suggest页面，跳过Schritt 4验证")
        else:
            return False, f"Schritt 4 页面加载失败: 未找到预期的Schritt 4 标题，实际h1内容: {h1_text}", None, None, None
    
    log_verbose(SCHRITT_4_LOGGER, "成功进入Schritt 4页面")
    
    # 在页面上进行操作：检查预约可用性
    # 检查当前URL，如果已经在suggest页面则直接使用当前响应
    if res.url.path.endswith('/suggest') or "suggest" in str(res.url):
        log_verbose(SCHRITT_4_LOGGER, "已经在suggest页面，使用当前响应")
        suggest_res = res
    else:
        # 否则发送GET请求到suggest页面
        suggest_url = urljoin(BASE_URL, 'suggest')
        suggest_res = session.get(suggest_url)
    
    # 检查是否有可用预约时间,没有直接返回。结束 function。
    if "Kein freier Termin verfügbar" in suggest_res.text:
        return False, "当前没有可用预约时间", None, None, None

    # ============================================================
    # 发现可用，这是关键信息，始终输出
    SCHRITT_4_LOGGER.info("发现可用预约时间")
    save_page_content(suggest_res.text, '4_term_available', location_name)

    # select_first_appointment now returns a datetime object
    success, message, form_data, appointment_datetime = select_first_appointment(suggest_res.text)
    if not success:
        return False, message, None, None, None

    # e.g. 可用预约时间 Mittwoch, 29.10.2025 16:00
    SCHRITT_4_LOGGER.info(f"可用预约时间 {appointment_datetime.strftime('%A, %d.%m.%Y %H:%M') if appointment_datetime else 'N/A'}")
    
    # ==================== ang ================================
    # Compare appointment date with configured cutoff date
    # if appointment_datetime and appointment_datetime.date() >= config.APPOINTMENT_CUTOFF_DATE:
    #     cutoff_str = config.APPOINTMENT_CUTOFF_DATE.strftime("%d.%m.%Y")
    #     return False, f"预约时间过晚: {appointment_datetime.strftime('%d.%m.%Y')} (截止: {cutoff_str})", None, None, None
    # ============================================================

    selected_profile = current_profile
    if not selected_profile:
        return False, "预约时间没有可用的profile", None, None, None

    return True, "Schritt 4 完成: 成功选择预约和profile", form_data, selected_profile, appointment_datetime

def enter_schritt_5_page(session: httpx.Client, form_data: dict, location_name: str, selected_profile: Optional[Profile]) -> Tuple[bool, str, Optional[bs4.BeautifulSoup]]:
    """
    进入Schritt 5页面并完成所有操作: 
    1. 提交预约选择
    2. 填写表单
    """
    log_verbose(SCHRITT_5_LOGGER, "成功进入Schritt 5页面")
    
    # 在页面上进行操作1：提交预约选择
    SCHRITT_5_LOGGER.info("Schritt 5: 正在提交预约选择...")
    
    submit_url = urljoin(BASE_URL, 'suggest')
    
    # 验证form_data内容
    if not form_data:
        SCHRITT_5_LOGGER.error("Schritt 5: form_data为空或None")
        return False, "Schritt 5: form_data为空", None
    
    # 设置适当的请求头
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': submit_url,
        'User-Agent': USER_AGENT
    }

    try:
        submit_res = session.post(submit_url, data=form_data, headers=headers, timeout=30.0)
    except httpx.TimeoutException as e:
        error_msg = f"Schritt 5 POST请求超时: {str(e)}"
        SCHRITT_5_LOGGER.error(error_msg)
        return False, error_msg, None
    except Exception as e:
        error_msg = f"Schritt 5 POST请求发生异常: {str(e)}"
        SCHRITT_5_LOGGER.error(error_msg)
        return False, error_msg, None

    # 检查superC服务器错误提示
    if "Fehlermeldung: Prozess fehlgeschlagen." in submit_res.text:
        SCHRITT_5_LOGGER.error("Schritt 5: superC server error")
        return True, "superC server error", None

    # 检查HTTP错误状态码
    if submit_res.status_code not in [200, 302]:
        error_msg = f"Schritt 5 POST请求失败，状态码: {submit_res.status_code}"
        SCHRITT_5_LOGGER.error(error_msg)
        return False, error_msg, None

    # 如果响应为空，记录详细信息
    if not submit_res.text.strip():
        error_msg = "Schritt 5 POST响应内容为空"
        SCHRITT_5_LOGGER.error(f"{error_msg}！")
        SCHRITT_5_LOGGER.error(f"状态码: {submit_res.status_code}")
        SCHRITT_5_LOGGER.error(f"响应头: {dict(submit_res.headers)}")
        SCHRITT_5_LOGGER.error(f"请求URL: {submit_res.url}")
        return False, error_msg, None

    save_page_content(submit_res.text, '5_term_selected', location_name)

    if not validate_page_step(submit_res, "5"):
        SCHRITT_5_LOGGER.warning("Schritt 5 失败: 提交时间后未进入Schritt 5，可能选择失败")
        return False, "Schritt 5 失败: 提交时间后未进入Schritt 5", None

    submit_soup = bs4.BeautifulSoup(submit_res.text, 'html.parser')
    SCHRITT_5_LOGGER.info("Schritt 5: 成功选择时间，现在填写表单...")
    
    # ============================================================
    # 在schritt 5 上进行操作2：填写表单
    # ============================================================
    if not selected_profile:
        return False, "Schritt 5页面填写表单失败: 未提供选择的profile", None

    SCHRITT_5_LOGGER.info(f"Schritt 5页面: 准备使用 {selected_profile.full_name} profile 填写表单...")
    
    # 使用带重试的表单填写函数
    result = fill_form_with_captcha_retry(session, submit_soup, location_name, selected_profile, max_retries=10)

    # 检查表单填写结果
    if result[0]:
        # 这是关键信息，始终输出
        SCHRITT_5_LOGGER.info("Schritt 5页面: 表单填写成功")
        return True, "Schritt 5 完成: 成功选择时间并填写表单", submit_soup
    else:
        return False, f"Schritt 5页面填写表单失败: {result[1]}", None

def enter_schritt_6_page(session: httpx.Client, soup: bs4.BeautifulSoup, location_name: str) -> Tuple[bool, str]:
    """
    进入Schritt 6页面并完成操作: 邮件确认 - 完成预约确认流程
    """
    log_verbose(SCHRITT_6_LOGGER, "成功进入Schritt 6页面")
    
    # 在页面上进行操作：处理邮件确认
    # 这里可能需要处理邮件确认步骤
    # 目前假设 fill_form 已经完成了所有必要的提交
    # 这是关键信息，始终输出
    SCHRITT_6_LOGGER.info("Schritt 6: 预约已完成，等待邮件确认")
    return True, "Schritt 6 完成: 预约已完成，等待邮件确认"
