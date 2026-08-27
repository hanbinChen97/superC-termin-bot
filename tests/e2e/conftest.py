"""
E2E Test Fixtures and Shared Utilities
=======================================

共用 fixtures:
- fixture_html(): 从 fixtures/ 目录加载 HTML 文件
- superc_location_config: SuperC 标准配置
- test_profile: 测试用 Profile（不触碰真实数据库）
"""

from pathlib import Path
import pytest
from superc.profile import Profile


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    """从 fixtures 目录读取 HTML 文件内容"""
    path = FIXTURES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return path.read_text(encoding="utf-8")


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
    """测试用 Profile，无需数据库"""
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
