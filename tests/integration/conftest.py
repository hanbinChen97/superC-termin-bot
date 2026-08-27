"""
Integration Test Fixtures
==========================

这一层的测试使用 vcrpy 录制/回放真实 HTTP 交互。

录制模式（第一次运行，需要真实网络）:
  PYTHONPATH=. pytest tests/integration/ -m integration --record-mode=new_episodes -v

回放模式（后续运行，无需网络）:
  PYTHONPATH=. pytest tests/integration/ -m integration -v

更新 cassette（真实网站结构变化时）:
  PYTHONPATH=. pytest tests/integration/ -m integration --record-mode=new_episodes -v
"""

import pytest
from pathlib import Path
from superc.profile import Profile


# ===== vcrpy 目录配置 =====
# cassette 文件统一存放在 tests/integration/cassettes/
@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    """将 cassette 文件统一存放在与测试文件相邻的 cassettes/ 目录"""
    return str(Path(request.fspath).parent / "cassettes")


@pytest.fixture
def superc_location_config() -> dict:
    """SuperC 地点标准配置"""
    return {
        "name": "superc",
        "selection_text": "Super C",
        "submit_text": "Ausländeramt Aachen - Außenstelle RWTH auswählen",
    }


@pytest.fixture
def test_profile() -> Profile:
    """测试用 Profile（只读阶段不会真正提交）"""
    return Profile(
        vorname="Max",
        nachname="Mustermann",
        email="max.mustermann@example.com",
        phone="0123456789",
        geburtsdatum_day=1,
        geburtsdatum_month=1,
        geburtsdatum_year=1990,
        preferred_locations="superc",
    )
