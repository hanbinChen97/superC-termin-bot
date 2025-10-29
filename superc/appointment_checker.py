"""
Appointment Checker Logic Flow

fold: cmd k + cmd 0
python -m superc.appointment_checker
"""


import httpx
import bs4
import logging
from typing import Tuple, Union, Optional
from datetime import date, datetime
import re
from urllib.parse import urljoin

# 使用相对导入
from . import config
from .utils.logging_utils import setup_logging
from .utils.utils import save_page_content, validate_page_step
from .utils.form_filler import fill_form_with_captcha_retry
import json
from .profile import Profile
from .utils.appointment_selector import select_first_appointment
from .utils.page_navigation import enter_schritt_2_page, enter_schritt_3_page, enter_schritt_4_page, enter_schritt_5_page, enter_schritt_6_page, log_verbose


SCHRITT_2_LOGGER = logging.getLogger("schritt2")
SCHRITT_3_LOGGER = logging.getLogger("schritt3")
SCHRITT_4_LOGGER = logging.getLogger("schritt4")
SCHRITT_5_LOGGER = logging.getLogger("schritt5")
SCHRITT_6_LOGGER = logging.getLogger("schritt6")


USER_AGENT = config.USER_AGENT
BASE_URL = config.BASE_URL


def run_check(location_config: dict, current_profile: Optional[Profile]) -> Tuple[bool, str, Optional[datetime]]:
    """
    执行一次完整的预约检查流程 - 6个Schritt步骤
    返回: (成功?, 消息, 预约日期时间对象)
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
        # logging.info(f"开始检查 {location_name} 的预约...")
        log_verbose(SCHRITT_2_LOGGER, "=== 进入Schritt 2页面 ===")

        # ===========================================================
        # 进入Schritt 2页面并完成操作
        # ===========================================================
        success, url = enter_schritt_2_page(session, location_config["selection_text"])
        if not success: 
            SCHRITT_2_LOGGER.error(f"Schritt 2页面失败: {url}")
            return False, url, None

        # ============================================================
        # 进入Schritt 3页面并完成操作
        # ===========================================================
        log_verbose(SCHRITT_3_LOGGER, "=== 进入Schritt 3页面 ===")
        success, loc = enter_schritt_3_page(session, url)
        if not success: 
            SCHRITT_3_LOGGER.error(f"Schritt 3 页面: {loc}")
            return False, str(loc), None

        # ============================================================
        # 进入Schritt 4页面并完成操作
        # ============================================================
        log_verbose(SCHRITT_4_LOGGER, "=== 进入Schritt 4页面 ===")
        success, message, form_data, selected_profile, appointment_datetime = enter_schritt_4_page(session, url, loc, location_config["submit_text"], location_name, current_profile)
        
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
        # ===========================================================
        # 进入Schritt 6页面并完成操作：邮件确认
        # ==========================================================
        if soup is None:
            return has_appointment, "内部错误：soup为空", None
            
        result = enter_schritt_6_page(session, soup, location_name)
        if result[0]:
            # 这是关键信息，始终输出
            SCHRITT_6_LOGGER.info(f"预约成功完成: {result[1]}")
            return has_appointment, result[1], appointment_datetime
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
    success, message, appointment_datetime = run_check(location_config, None)
    
    print(f"检查结果: {'成功' if success else '失败'} - {message}")

    if appointment_datetime:
        print(f"预约时间: {appointment_datetime.strftime('%Y-%m-%d %H:%M')}")
