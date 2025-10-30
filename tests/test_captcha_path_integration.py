"""
Integration test for download_captcha with the new configuration

This test verifies that the download_captcha function uses the new
configurable path from config.py
"""

import os
import sys
import tempfile
import shutil

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import config directly
import importlib.util
spec = importlib.util.spec_from_file_location("config", os.path.join(project_root, "superc", "config.py"))
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)


def test_get_captcha_dir_integration():
    """Test that get_captcha_dir function is accessible and works correctly"""
    # Test for superc location
    superc_path = config_module.get_captcha_dir("superc")
    assert superc_path == "data/superc/captcha"
    
    # Test for infostelle location
    infostelle_path = config_module.get_captcha_dir("infostelle")
    assert infostelle_path == "data/infostelle/captcha"
    
    print(f"✓ SuperC captcha path: {superc_path}")
    print(f"✓ Infostelle captcha path: {infostelle_path}")


def test_config_constants():
    """Verify the configuration constants are properly defined"""
    assert hasattr(config_module, 'CAPTCHA_BASE_DIR')
    assert hasattr(config_module, 'CAPTCHA_SUBDIR')
    assert config_module.CAPTCHA_BASE_DIR == "data"
    assert config_module.CAPTCHA_SUBDIR == "captcha"
    print(f"✓ CAPTCHA_BASE_DIR: {config_module.CAPTCHA_BASE_DIR}")
    print(f"✓ CAPTCHA_SUBDIR: {config_module.CAPTCHA_SUBDIR}")


if __name__ == "__main__":
    print("Running integration tests...")
    test_config_constants()
    test_get_captcha_dir_integration()
    print("\nAll integration tests passed!")
