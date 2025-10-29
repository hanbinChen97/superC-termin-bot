"""
Appointment Selection Logic

This module handles the logic for selecting the first available appointment from
the suggest page.

pytest superc/utils/appointment_selector.py
"""

import bs4
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict
from datetime import datetime


logger = logging.getLogger(__name__)


def select_first_appointment(suggest_res_text: str) -> Tuple[bool, str, Optional[Dict[str, str]], Optional[datetime]]:
    """
    选择页面中的第一个可用预约并返回其表单数据和datetime对象
    返回: (成功?, 消息, form_data, 预约日期时间对象)
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

    form_data = {inp.get('name'): inp.get('value') for inp in first_available_form.find_all("input", {"type": "hidden"})}

    date_str = form_data.get("date")  # YYYYMMDD
    time_button = first_available_form.find("button", {"type": "submit"})
    time_str = time_button.get('title') if time_button else None # HH:MM

    if not date_str or not time_str:
        return False, "无法从表单中可靠地确定预约日期/时间。", None, None

    try:
        # Combine date and time and parse into a datetime object
        appointment_dt = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H:%M")
        logger.info(f"找到可用时间: {appointment_dt.strftime('%A, %d.%m.%Y %H:%M')}")
        return True, "成功解析预约信息", form_data, appointment_dt
    except (ValueError, TypeError) as e:
        logger.error(f"解析日期/时间时出错: date='{date_str}', time='{time_str}'. 错误: {e}")
        return False, "无法解析预约日期或时间", None, None


def test_select_first_appointment_from_saved_page():
    # data/debugPage/step_4_term_available_20251003_152049.html
    # Assuming the test is run from the project root.
    html_path = Path("data/debugPage/step_4_term_available_20251003_152049.html")
    if not html_path.exists():
        # If not in root, try to go up from current file.
        html_path = Path(__file__).resolve().parent.parent.parent / "data/debugPage/step_4_term_available_20251003_152049.html"

    if not html_path.exists():
        print(f"Test file not found at {html_path}, skipping test.")
        return

    suggest_html = html_path.read_text(encoding="utf-8")

    success, message, form_data, appointment_datetime = select_first_appointment(suggest_html)

    print(f"Form data: {form_data}")
    print(f"Appointment datetime: {appointment_datetime}")
    
    assert success, message
    assert form_data is not None
    assert form_data.get("date") == "20251211"
    assert appointment_datetime is not None
    assert appointment_datetime.date() == datetime(2025, 12, 11).date()