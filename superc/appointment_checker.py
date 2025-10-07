"""
Appointment Checker Logic Flow

fold: cmd k + cmd 0
python -m superc.appointment_checker
"""


import httpx
import bs4
import logging
from typing import Tuple, Union, Optional
from urllib.parse import urljoin

# 使用相对导入
from . import config
from .logging_utils import setup_logging
from .utils import save_page_content, validate_page_step
from .form_filler import fill_form_with_captcha_retry
from datetime import datetime
import json
from .profile import Profile
from .appointment_selector import select_first_appointment


SCHRITT_2_LOGGER = logging.getLogger("schritt2")
SCHRITT_3_LOGGER = logging.getLogger("schritt3")
SCHRITT_4_LOGGER = logging.getLogger("schritt4")
SCHRITT_5_LOGGER = logging.getLogger("schritt5")
SCHRITT_6_LOGGER = logging.getLogger("schritt6")


USER_AGENT = config.USER_AGENT
BASE_URL = config.BASE_URL


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
    log_verbose(SCHRITT_2_LOGGER, "Schritt 2 完成: 成功选择服务类型")
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

def enter_schritt_4_page(session: httpx.Client, url: str, loc: str, submit_text: str, location_name: str, current_profile: Optional[Profile]) -> Tuple[bool, str, Optional[dict], Optional[Profile], Optional[str]]:
    """
    进入Schritt 4页面并完成操作: 检查预约时间可用性并选择第一个可用时间，同时选择合适的profile
    返回: (成功?, 消息, form_data, 选择的profile, 预约日期时间字符串)
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
        
        # 添加调试信息
        # log_verbose(SCHRITT_4_LOGGER, f"Schritt 4 请求后状态码: {res.status_code}")
        # log_verbose(SCHRITT_4_LOGGER, f"Schritt 4 最终URL: {res.url}")
        # log_verbose(SCHRITT_4_LOGGER, f"响应内容长度: {len(res.text)}")
        # log_verbose(SCHRITT_4_LOGGER, f"重定向历史: {[str(r.url) for r in res.history]}")
        
        # 保存页面内容用于调试
        # save_page_content(res.text, '4_after_redirect', location_name)
        
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
    
    log_verbose("成功进入Schritt 4页面")
    
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

    # 选择第一个可用预约
    success, message, form_data, appointment_datetime_str = select_first_appointment(suggest_res.text)
    SCHRITT_4_LOGGER.info(f"可用预约时间 {appointment_datetime_str}")

    if not success:
        return False, message, None, None, None

    selected_profile = current_profile
    if not selected_profile:
        return False, "预约时间没有可用的profile", None, None, None

    return True, "Schritt 4 完成: 成功选择预约和profile", form_data, selected_profile, appointment_datetime_str

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
    
    # 添加详细的调试信息
    # SCHRITT_5_LOGGER.info(f"Schritt 5 POST请求URL: {submit_url}")
    # SCHRITT_5_LOGGER.info(f"Schritt 5 POST请求数据类型: {type(form_data)}")
    # SCHRITT_5_LOGGER.info(f"Schritt 5 POST请求数据字段数: {len(form_data)}")
    # SCHRITT_5_LOGGER.info(f"Schritt 5 POST请求数据内容: {form_data}")
    
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

    # 记录响应状态
    # SCHRITT_5_LOGGER.info(f"Schritt 5 POST响应状态码: {submit_res.status_code}")
    # SCHRITT_5_LOGGER.info(f"Schritt 5 POST响应头: {dict(submit_res.headers)}")
    # SCHRITT_5_LOGGER.info(f"Schritt 5 POST响应内容长度: {len(submit_res.text)}")

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

def run_check(location_config: dict, current_profile: Optional[Profile]) -> Tuple[bool, str, Optional[str]]:
    """
    执行一次完整的预约检查流程 - 6个Schritt步骤
    返回: (成功?, 消息, 预约日期时间字符串)
    """
    # 创建session并配置适当的超时和重试策略
    session = httpx.Client(
        timeout=30.0,
        follow_redirects=True,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
    session.headers.update({"User-Agent": USER_AGENT})
    location_name = location_config["name"]
    
    try:
        # 这是关键信息，始终输出
        # logging.info(f"开始检查 {location_name} 的预约...")
        log_verbose(SCHRITT_2_LOGGER, "=== 进入Schritt 2页面 ===")

        # 进入Schritt 2页面并完成操作
        success, url = enter_schritt_2_page(session, location_config["selection_text"])
        if not success: 
            SCHRITT_2_LOGGER.error(f"Schritt 2页面失败: {url}")
            return False, url, None

        log_verbose(SCHRITT_3_LOGGER, "=== 进入Schritt 3页面 ===")
        # 进入Schritt 3页面并完成操作
        success, loc = enter_schritt_3_page(session, url)
        if not success: 
            SCHRITT_3_LOGGER.error(f"Schritt 3 页面: {loc}")
            return False, str(loc), None

        # ============================================================
        # 进入Schritt 4页面并完成操作
        # ============================================================
        log_verbose(SCHRITT_4_LOGGER, "=== 进入Schritt 4页面 ===")
        success, message, form_data, selected_profile, appointment_datetime_str = enter_schritt_4_page(session, url, loc, location_config["submit_text"], location_name, current_profile)
        
        if not success:
            SCHRITT_4_LOGGER.info(f"Schritt 4 page: {message}")
            return False, message, None
        else:
            SCHRITT_4_LOGGER.info(f"Schritt 4  page 有预约: {message}")

        has_appointment = True


        # ============================================================
        # 进入Schritt 5页面并完成所有操作：提交预约选择 + 填写表单
        # form_data 里面包含了所有信息，appointment_datetime_str 只是为了显示用。
        # ============================================================
        log_verbose(SCHRITT_5_LOGGER, "=== 进入Schritt 5页面 ===")
        if form_data is None or selected_profile is None:
            return has_appointment, "内部错误：form_data或selected_profile为空", None
            
        success, message, soup = enter_schritt_5_page(session, form_data, location_name, selected_profile)

        if message == "superC server error":
            SCHRITT_5_LOGGER.error("Schritt 5: superC server error，停止本轮流程")
            return has_appointment, message, None

        if not success:
            SCHRITT_5_LOGGER.error(f"Schritt 5页面失败: {message}")
            return has_appointment, message, None


        log_verbose(SCHRITT_6_LOGGER, "=== 进入Schritt 6页面 ===")
        # 进入Schritt 6页面并完成操作：邮件确认
        if soup is None:
            return has_appointment, "内部错误：soup为空", None
            
        result = enter_schritt_6_page(session, soup, location_name)
        if result[0]:
            # 这是关键信息，始终输出
            SCHRITT_6_LOGGER.info(f"预约成功完成: {result[1]}")
            return has_appointment, result[1], appointment_datetime_str
        else:
            SCHRITT_6_LOGGER.error(f"Schritt 6 失败: {result[1]}")
            return has_appointment, result[1], None

    finally:
        # 确保session正确关闭
        session.close()

if __name__ == "__main__":
    setup_logging(force=True)

    location_config = {
        "name": "superc",
        "selection_text": "Super C",
        "submit_text": "Ausländeramt Aachen - Außenstelle RWTH auswählen"
    }
    
    # 为测试提供 None 的 profile 参数
    success, message, appointment_datetime_str = run_check(location_config, None)
    
    print(f"检查结果: {'成功' if success else '失败'} - {message}")

    if appointment_datetime_str:
        print(f"预约时间: {appointment_datetime_str}")
