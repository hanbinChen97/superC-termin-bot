"""
Appointment Selection Logic

This module handles the logic for selecting the first available appointment from
the suggest page.

pytest superc/appointment_selector.py
"""

import bs4
import logging
from pathlib import Path
from typing import Tuple, Optional


def select_first_appointment(suggest_res_text: str) -> Tuple[bool, str, Optional[dict], Optional[str]]:
    """
    选择页面中的第一个可用预约并返回其表单数据
    返回: (成功?, 消息, form_data, 预约日期时间字符串)
    """
    soup = bs4.BeautifulSoup(suggest_res_text, 'html.parser')
    details_container = soup.find("details", {"id": "details_suggest_times"})
    if not details_container:
        details_container = soup.find("div", {"id": "sugg_accordion"})

    if not details_container:
        return False, "在预约页面找不到时间容器", None, None

    first_available_form = details_container.find("form", {"class": "suggestion_form"})

    if not first_available_form:
        return False, "有可用时间但无法找到具体的预约表单", None, None

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

    # 时间来自 <button>
    time_button = first_available_form.find("button", {"type": "submit"})
    time_info = time_button.get('title') if time_button else "未知时间"

    # 确保 time_info 是字符串
    if time_info is None or not isinstance(time_info, str):
        time_info = "未知时间"

    # 组合完整的预约日期时间字符串
    appointment_datetime_str = f"{date_display} {time_info}" if time_info != "未知时间" else str(date_display)

    # 这是关键信息，始终输出
    logging.info(f"找到可用时间: {appointment_datetime_str}")

    return True, "成功解析预约信息", form_data, appointment_datetime_str


def test_select_first_appointment_from_saved_page():
    html_path = Path(__file__).resolve().parent.parent / "data/pages/superc/step_4_term_available_20251003_152052.html"
    suggest_html = html_path.read_text(encoding="utf-8")

    success, message, form_data, appointment_datetime = select_first_appointment(suggest_html)

    print(form_data)
    print(appointment_datetime)
    
    assert success, message
    assert form_data is not None
    assert form_data.get("date") == "20251211"
    assert appointment_datetime
    assert "Donnerstag" in appointment_datetime
