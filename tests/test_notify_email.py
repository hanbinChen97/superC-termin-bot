"""
Unit tests for email notification module.

Tests email sending functionality including:
- Email content generation
- SMTP connection and sending
- Error handling
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superc.notify_email import get_email_content, send_notify_email


class EmailNotificationTests(unittest.TestCase):
    """Test cases for email notification functionality"""
    
    def test_get_email_content_with_complete_info(self):
        """Test email content generation with complete appointment info"""
        appointment_info = {
            'name': 'Test User',
            'appointment_datetime': '2024-10-15 10:00',
            'location': 'SuperC'
        }
        
        subject, html_body = get_email_content(appointment_info)
        
        # Verify subject
        self.assertIn('预约成功', subject)
        self.assertIn('SuperC', subject)
        
        # Verify body contains key information
        self.assertIn('Test User', html_body)
        self.assertIn('2024-10-15 10:00', html_body)
        self.assertIn('SuperC', html_body)
        self.assertIn('打赏', html_body)  # Donation information
        self.assertIn('确认邮件', html_body)  # Confirmation reminder
    
    def test_get_email_content_with_missing_info(self):
        """Test email content generation with missing appointment info"""
        appointment_info = {}
        
        subject, html_body = get_email_content(appointment_info)
        
        # Verify defaults are used
        self.assertIn('预约成功', subject)
        self.assertIn('用户', html_body)  # Default name
        self.assertIn('待确认', html_body)  # Default datetime
    
    @patch.dict(os.environ, {
        'SMTP_SERVER': 'smtp.test.com',
        'SMTP_PORT': '465',
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'password',
        'SMTP_SENDER': 'sender@test.com'
    })
    @patch('superc.notify_email.smtplib.SMTP_SSL')
    def test_send_notify_email_success(self, mock_smtp):
        """Test successful email sending"""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        appointment_info = {
            'name': 'Test User',
            'appointment_datetime': '2024-10-15 10:00',
            'location': 'SuperC'
        }
        
        result = send_notify_email('test@example.com', appointment_info)
        
        # Verify email was sent
        self.assertTrue(result)
        mock_server.login.assert_called_once_with('test@test.com', 'password')
        mock_server.send_message.assert_called_once()
    
    @patch.dict(os.environ, {
        'SMTP_SERVER': '',
        'SMTP_USER': '',
        'SMTP_PASSWORD': ''
    })
    def test_send_notify_email_missing_config(self):
        """Test email sending with missing SMTP configuration"""
        appointment_info = {
            'name': 'Test User',
            'appointment_datetime': '2024-10-15 10:00',
            'location': 'SuperC'
        }
        
        result = send_notify_email('test@example.com', appointment_info)
        
        # Should return False when config is missing
        self.assertFalse(result)
    
    @patch.dict(os.environ, {
        'SMTP_SERVER': 'smtp.test.com',
        'SMTP_PORT': '465',
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'password'
    })
    def test_send_notify_email_invalid_email(self):
        """Test email sending with invalid email address"""
        appointment_info = {
            'name': 'Test User',
            'appointment_datetime': '2024-10-15 10:00',
            'location': 'SuperC'
        }
        
        # Test with invalid email
        result = send_notify_email('invalid-email', appointment_info)
        self.assertFalse(result)
        
        # Test with empty email
        result = send_notify_email('', appointment_info)
        self.assertFalse(result)
    
    @patch.dict(os.environ, {
        'SMTP_SERVER': 'smtp.test.com',
        'SMTP_PORT': '465',
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'wrong_password',
        'SMTP_SENDER': 'sender@test.com'
    })
    @patch('superc.notify_email.smtplib.SMTP_SSL')
    def test_send_notify_email_auth_failure(self, mock_smtp):
        """Test email sending with authentication failure"""
        # Setup mock to raise authentication error
        import smtplib
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        appointment_info = {
            'name': 'Test User',
            'appointment_datetime': '2024-10-15 10:00',
            'location': 'SuperC'
        }
        
        result = send_notify_email('test@example.com', appointment_info)
        
        # Should return False on authentication failure
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
