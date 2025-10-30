"""
Tests for configuration module, particularly CAPTCHA path configuration

Run with: PYTHONPATH=. pytest tests/test_config.py
"""

import pytest
import sys
import os

# Add project root to path for direct config import
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import config directly without going through __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location("config", os.path.join(project_root, "superc", "config.py"))
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

get_captcha_dir = config.get_captcha_dir
CAPTCHA_BASE_DIR = config.CAPTCHA_BASE_DIR
CAPTCHA_SUBDIR = config.CAPTCHA_SUBDIR


def test_captcha_base_dir_constant():
    """Test that CAPTCHA_BASE_DIR constant is defined"""
    assert CAPTCHA_BASE_DIR == "data"


def test_captcha_subdir_constant():
    """Test that CAPTCHA_SUBDIR constant is defined"""
    assert CAPTCHA_SUBDIR == "captcha"


def test_get_captcha_dir_superc():
    """Test get_captcha_dir returns correct path for superc location"""
    result = get_captcha_dir("superc")
    assert result == "data/superc/captcha"


def test_get_captcha_dir_infostelle():
    """Test get_captcha_dir returns correct path for infostelle location"""
    result = get_captcha_dir("infostelle")
    assert result == "data/infostelle/captcha"


def test_get_captcha_dir_format():
    """Test get_captcha_dir returns path in expected format"""
    location = "test_location"
    result = get_captcha_dir(location)
    
    # Verify format: CAPTCHA_BASE_DIR/location_name/CAPTCHA_SUBDIR
    expected = f"{CAPTCHA_BASE_DIR}/{location}/{CAPTCHA_SUBDIR}"
    assert result == expected
    assert result.startswith(CAPTCHA_BASE_DIR)
    assert location in result
    assert result.endswith(CAPTCHA_SUBDIR)


def test_get_captcha_dir_type():
    """Test get_captcha_dir returns a string"""
    result = get_captcha_dir("superc")
    assert isinstance(result, str)


def test_get_captcha_dir_no_trailing_slash():
    """Test get_captcha_dir doesn't add unnecessary trailing slashes"""
    result = get_captcha_dir("superc")
    assert not result.endswith("/")
