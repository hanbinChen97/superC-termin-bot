"""
Integration Test: 真实网络 Schritt 2-3 只读验证
================================================

用 vcrpy 录制真实 HTTP 对话，之后离线回放。
只测到 Schritt 3，不进入预约提交流程。

【第一次运行 - 录制模式，需要真实网络】
  PYTHONPATH=. pytest tests/integration/ -m integration --record-mode=new_episodes -v

【后续运行 - 回放模式，完全离线】
  PYTHONPATH=. pytest tests/integration/ -m integration -v

【强制重新录制（网站结构变化时）】
  PYTHONPATH=. pytest tests/integration/ -m integration --record-mode=all -v

【cassette 存储位置】
  tests/integration/cassettes/<test_name>.yaml
"""

import httpx
import pytest

from superc import config
from superc.utils.page_navigation import enter_schritt_2_page, enter_schritt_3_page


BASE_URL = config.BASE_URL
USER_AGENT = config.USER_AGENT


def _make_session() -> httpx.Client:
    """创建与真实 run_check 相同配置的 httpx session"""
    session = httpx.Client(
        timeout=30.0,
        follow_redirects=True,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
    )
    session.headers.update({"User-Agent": USER_AGENT})
    return session


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["cookie", "set-cookie", "authorization"])
def test_schritt2_page_structure():
    """
    验证 Schritt 2 页面结构未发生变化：
    - 页面标题含 "Schritt 2"
    - 存在 "Super C" 选项
    - 能成功提取 cnc-{id} 并生成下一步 URL
    """
    session = _make_session()
    try:
        success, result = enter_schritt_2_page(session, "Super C")
    finally:
        session.close()

    assert success is True, f"Schritt 2 失败: {result}"
    assert "location" in result, f"生成的 URL 不含 'location': {result}"
    assert "cnc-" in result, f"生成的 URL 不含 cnc 参数: {result}"


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["cookie", "set-cookie", "authorization"])
def test_schritt3_extracts_loc(superc_location_config):
    """
    验证 Schritt 2→3 数据传递正确：
    - Schritt 2 生成有效的 URL
    - Schritt 3 能从真实页面提取 loc 值
    - loc 值非空
    """
    session = _make_session()
    try:
        # Step 1: 获取 Schritt 3 URL
        success_2, url = enter_schritt_2_page(session, superc_location_config["selection_text"])
        assert success_2, f"Schritt 2 前置失败: {url}"

        # Step 2: 进入 Schritt 3
        success_3, loc = enter_schritt_3_page(session, url)
    finally:
        session.close()

    assert success_3 is True, f"Schritt 3 失败: {loc}"
    assert loc, "loc 值为空"
