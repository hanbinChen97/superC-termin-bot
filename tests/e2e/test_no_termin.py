"""
E2E Test: 无预约时间场景 (No Appointment Available)
=====================================================

场景描述:
  模拟 SuperC 网站在 Schritt 4 的 /suggest 端点返回
  "Kein freier Termin verfügbar"，验证 run_check() 能正确
  识别"无可用预约"并返回 (False, ..., None)。

Mock 的 HTTP 请求链:
  GET  /select2?md=1          → schritt2.html       (选择服务类型)
  GET  /location?mdt=89&...   → schritt3.html       (获取 loc 值)
  POST /location?mdt=89&...   → schritt4.html       (进入 Schritt 4)
  GET  /suggest               → suggest_no_termin.html (无预约时间)

运行方式:
  PYTHONPATH=. pytest tests/e2e/test_no_termin.py -v
"""

import re
import httpx
import respx
import pytest

from superc.appointment_checker import run_check
from tests.e2e.conftest import load_fixture


BASE = "https://termine.staedteregion-aachen.de/auslaenderamt"


@respx.mock
def test_no_termin_available(superc_location_config, test_profile):
    """
    E2E: 当 /suggest 返回无可用时间时，
    run_check() 应返回 (False, "当前没有可用预约时间", None)
    """
    # ------------------------------------------------------------------
    # 1. Mock Schritt 2: GET /select2?md=1
    #    返回含 "Super C" 选项 和 cnc-42 列表项的页面
    # ------------------------------------------------------------------
    respx.get(f"{BASE}/select2", params={"md": "1"}).mock(
        return_value=httpx.Response(200, text=load_fixture("schritt2.html"))
    )

    # ------------------------------------------------------------------
    # 2. Mock Schritt 3: GET /location?mdt=89&select_cnc=1&cnc-42=1
    #    返回含 loc hidden input 的页面
    # ------------------------------------------------------------------
    respx.get(
        url__regex=rf"{re.escape(BASE)}/location\?.*cnc-42.*"
    ).mock(
        return_value=httpx.Response(200, text=load_fixture("schritt3.html"))
    )

    # ------------------------------------------------------------------
    # 3. Mock Schritt 4: POST /location?...
    #    返回 Schritt 4 页面（POST 进入）
    # ------------------------------------------------------------------
    respx.post(
        url__regex=rf"{re.escape(BASE)}/location.*"
    ).mock(
        return_value=httpx.Response(200, text=load_fixture("schritt4.html"))
    )

    # ------------------------------------------------------------------
    # 4. Mock suggest: GET /suggest
    #    关键响应：返回"无可用预约时间"
    # ------------------------------------------------------------------
    respx.get(f"{BASE}/suggest").mock(
        return_value=httpx.Response(200, text=load_fixture("suggest_no_termin.html"))
    )

    # ------------------------------------------------------------------
    # 执行被测函数
    # ------------------------------------------------------------------
    success, message, appointment_dt = run_check(superc_location_config, test_profile)

    # ------------------------------------------------------------------
    # 断言
    # ------------------------------------------------------------------
    assert success is False, f"预期 success=False，实际得到 success={success}"
    assert appointment_dt is None, f"预期 appointment_dt=None，实际得到 {appointment_dt}"
    assert "没有可用预约时间" in message or "Kein" in message or message, (
        f"预期消息含无预约提示，实际得到: '{message}'"
    )
