# -*- coding: utf-8 -*-
"""
Integration tests for appointment checking functionality.

These tests may require network access and external dependencies.
"""

import sys
import os

# Add the parent directory to the path so we can import the superc package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch
import requests

from superc.appointment_checker import get_initial_page, select_location_type
from superc.config import LOCATIONS


class TestAppointmentChecker:
    """Integration tests for the appointment checking functionality."""
    
    def test_get_initial_page_structure(self):
        """Test that get_initial_page returns expected structure."""
        with patch('superc.appointment_checker.requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.content = b"<html><body>Test</body></html>"
            mock_session.get.return_value = mock_response
            
            success, response = get_initial_page(mock_session)
            
            assert success is True
            assert response == mock_response


    def test_select_location_type_structure(self):
        """Test that select_location_type can handle basic HTML structure."""
        with patch('superc.appointment_checker.requests.Session') as mock_session_class:
            mock_session = Mock()
            
            # Mock HTML content that would be expected from the site
            mock_html = """
            <html>
                <body>
                    <h3>Super C Test</h3>
                    <div>
                        <ul>
                            <li id="test-123">Option 1</li>
                        </ul>
                    </div>
                </body>
            </html>
            """
            mock_response = Mock()
            mock_response.content = mock_html
            
            success, result = select_location_type(mock_session, mock_response, "Super C")
            
            # The function should find the header and construct a URL
            assert success is True
            assert "cnc-123" in result


if __name__ == "__main__":
    # Run integration tests manually if executed directly
    import unittest
    unittest.main()