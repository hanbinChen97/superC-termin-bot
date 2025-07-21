# -*- coding: utf-8 -*-

import requests
import bs4
import logging
from urllib.parse import urljoin

from .form_filler import fill_form
from .utils import save_page_content, download_captcha
from .config import BASE_URL, USER_AGENT

def get_initial_page(session):
    """
    获取初始页面 (Schritt 1 & 2)
    """
    url = urljoin(BASE_URL, 'select2?md=1')
    res = session.get(url)
    # logging.info("成功获取初始页面")
    return True, res

def select_location_type(session, res, selection_text):
    """
    根据文本选择预约地点类型 (z.B. Super C oder Infostelle)
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
    # logging.info(f"成功构建地点类型URL: {url}")
    return True, url

def get_location_info(session, url):
    """
    获取并确认位置信息 (Schritt 3)
    """
    res = session.get(url)
    soup = bs4.BeautifulSoup(res.content, 'html.parser')
    loc = soup.find('input', {'name': 'loc'})
    if not loc:
        return False, "无法在页面上找到位置信息 'loc'"
    
    # logging.info("成功获取位置信息")
    return True, (loc.get('value'), res)

def submit_location(session, url, loc, submit_text):
    """
    提交位置信息
    """
    payload = {
        'loc': str(loc),
        'gps_lat': '55.77858',
        'gps_long': '65.07867',
        'select_location': submit_text
    }
    res = session.post(url, data=payload)
    # logging.info("成功提交位置信息")
    return True, res

def find_and_select_appointment(session, location_name):
    """
    检查是否有可用预约时间，并自动选择第一个 (Schritt 4 & 5)
    """
    url = urljoin(BASE_URL, 'suggest')
    res = session.get(url)
    # save_page_content(res.text, '4_availability', location_name)

    if "Kein freier Termin verfügbar" in res.text:
        return False, "查询完成，当前没有可用预约时间", None

    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    details_container = soup.find("details", {"id": "details_suggest_times"})
    if not details_container:
        details_container = soup.find("div", {"id": "sugg_accordion"})

    if not details_container:
        return False, "在预约页面找不到时间容器", None

    logging.info("发现可用预约时间")
    
    first_available_form = details_container.find("form", {"class": "suggestion_form"})

    if not first_available_form:
        return False, "有可用时间但无法找到具体的预约表单", None

    # 从表单的隐藏字段中提取所有需要提交的数据
    form_data = {inp.get('name'): inp.get('value') for inp in first_available_form.find_all("input", {"type": "hidden"})}
    
    # 为了日志记录，提取可读的日期和时间
    # 日期来自 <summary>
    date_display = ""
    summary_tag = details_container.find("summary")
    if summary_tag:
        date_display = summary_tag.text.strip()

    # 根据日期决定使用哪个个人信息文件
    import config # 导入 config 模块以修改其变量
    try:
        # 从 "Mittwoch, 27.08.2025" 中提取 "dd.mm.yyyy" 部分
        date_part = date_display.split(', ')[1] 
        day, month, year = date_part.split('.')
        month_int = int(month)
        
        if month_int < 9:
            config.PERSONAL_INFO_FILE = "hanbin"
            logging.info(f"预约日期为 {date_display}，月份早于9月，将使用 'hanbin' 文件中的个人信息。")
        else:
            logging.info(f"预约日期为 {date_display}，月份为9月或更晚，跳过此预约。")
            return False, f"预约时间 {date_display} 不符合要求（仅处理9月前的预约）", None

    except (IndexError, ValueError) as e:
        logging.warning(f"无法从 '{date_display}' 解析日期，将使用默认的 'table' 文件。错误: {e}")
        config.PERSONAL_INFO_FILE = "table"
    
    # 时间来自 <button>
    time_button = first_available_form.find("button", {"type": "submit"})
    time_info = time_button.get('title') if time_button else "未知时间"

    # 如果 summary 中没有日期，可以尝试从 form_data 中获取
    if not date_display:
        date_display = form_data.get("date", "未知日期")

    logging.info(f"找到可用时间: {date_display} {time_info}, 正在提交...")
    
    submit_url = urljoin(BASE_URL, 'suggest')
    submit_res = session.post(submit_url, data=form_data)
    save_page_content(submit_res.text, '5_term_selected', location_name)

    if "Schritt 5" not in submit_res.text:
        logging.warning("提交时间后未进入步骤5，可能选择失败")
        return False, "提交时间后未进入步骤5", None

    submit_soup = bs4.BeautifulSoup(submit_res.text, 'html.parser')
    return True, "成功选择时间，准备填写表单", submit_soup

def complete_booking(session, soup, location_name):
    """
    下载验证码并填写最终表单 (Schritt 6)
    """
    success, captcha_path = download_captcha(session, soup, location_name)

    if not success:
        return False, captcha_path # 返回错误信息

    logging.info("准备填写最终表单...")
    return fill_form(session, soup, captcha_path, location_name)

def run_check(location_config):
    """
    执行一次完整的预约检查流程
    """
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    location_name = location_config["name"]

    # 流程编排
    success, res = get_initial_page(session)
    if not success: return False, res

    success, url = select_location_type(session, res, location_config["selection_text"])
    if not success: return False, url

    success, result = get_location_info(session, url)
    if not success: return False, result
    loc, res = result

    success, res = submit_location(session, url, loc, location_config["submit_text"])
    if not success: return False, res

    # 调用新的拆分后的函数
    success, message, soup = find_and_select_appointment(session, location_name)
    if not success:
        return False, message

    return complete_booking(session, soup, location_name)