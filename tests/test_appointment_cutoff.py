"""
Test appointment date parsing and cutoff comparison.

python3 -m pytest tests/test_appointment_cutoff.py -v

"""

from superc.appointment_checker import parse_appointment_date
from superc import config


def test_parse_from_display_string():
    """测试从显示字符串中解析日期 (输入: form=None, dt_str=str; 输出: date)"""
    form = None
    dt_str = "Mittwoch, 29.10.2025 16:00"

    appt_date = parse_appointment_date(form, dt_str)
    assert appt_date is not None, "应该能从显示字符串中解析出日期"
    assert appt_date.year == 2025
    assert appt_date.month == 10
    assert appt_date.day == 29


def test_parse_from_form_data():
    """测试从form_data隐藏字段中解析日期 (输入: form=dict, dt_str=None; 输出: date)"""
    form_data = {"date": "20251029"}
    dt_str = None

    appt_date = parse_appointment_date(form_data, dt_str)
    assert appt_date is not None, "应该能从form_data中解析出日期"
    assert appt_date.year == 2025
    assert appt_date.month == 10
    assert appt_date.day == 29


def test_compare_with_cutoff():
    """测试预约日期与截止日期的比较 (输入: dt_str=str; 输出: bool)"""
    dt_str = "Mittwoch, 29.10.2025 16:00"
    appt_date = parse_appointment_date(None, dt_str)

    # 29.10.2025 应严格早于 05.11.2025
    assert appt_date < config.APPOINTMENT_CUTOFF_DATE


def test_cutoff_date_boundary():
    """测试截止日期边界情况 (输入: dt_str=str; 输出: bool)"""
    # 测试截止日期当天应该被拒绝
    dt_str_on_cutoff = "Dienstag, 05.11.2025 10:00"
    appt_date_on_cutoff = parse_appointment_date(None, dt_str_on_cutoff)
    assert appt_date_on_cutoff >= config.APPOINTMENT_CUTOFF_DATE

    # 测试截止日期之后应该被拒绝
    dt_str_after_cutoff = "Mittwoch, 06.11.2025 10:00"
    appt_date_after = parse_appointment_date(None, dt_str_after_cutoff)
    assert appt_date_after >= config.APPOINTMENT_CUTOFF_DATE
