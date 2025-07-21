# -*- coding: utf-8 -*-
"""
Tests for the SuperC Termin Bot package

This module contains integration and unit tests for the appointment checking functionality.
"""

import sys
import os

# Add the parent directory to the path so we can import the superc package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch

from superc import LOCATIONS, LOG_FORMAT
from superc.config import BASE_URL, USER_AGENT


def test_config_constants():
    """Test that configuration constants are properly defined."""
    assert BASE_URL is not None
    assert USER_AGENT is not None
    assert LOG_FORMAT is not None
    assert "superc" in LOCATIONS
    assert "infostelle" in LOCATIONS


def test_locations_structure():
    """Test that location configurations have required fields."""
    for location_name, config in LOCATIONS.items():
        assert "name" in config
        assert "selection_text" in config
        assert "submit_text" in config
        assert config["name"] == location_name


@patch('superc.appointment_checker.requests.Session')
def test_import_functionality(mock_session):
    """Test that the main functionality can be imported without errors."""
    from superc.appointment_checker import run_check
    
    # This is a basic smoke test to ensure imports work
    assert callable(run_check)


if __name__ == "__main__":
    # Run basic tests manually if executed directly
    test_config_constants()
    test_locations_structure()
    print("Basic tests passed!")