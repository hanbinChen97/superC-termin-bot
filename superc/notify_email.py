"""
Email notification module for appointment booking system.

Sends notification emails to users after successful appointment booking,
including appointment details and donation information.

Input types:
- user_email: str - The email address of the user to notify
- appointment_info: dict - Dictionary containing appointment details
  Expected keys:
  - 'name': str - Full name of the user
  - 'appointment_datetime': str - Appointment date and time
  - 'location': str - Location type (e.g., 'superc', 'infostelle')

Output types:
- Returns: bool - True if email sent successfully, False otherwise
"""

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger("notify_email")


def get_email_content(appointment_info: dict) -> tuple[str, str]:
    """
    Generate email subject and body content.
    
    Input types:
    - appointment_info: dict - Dictionary containing appointment details
    
    Output types:
    - tuple[str, str] - (subject, html_body)
    """
    name = appointment_info.get('name', '用户')
    appointment_datetime = appointment_info.get('appointment_datetime', '待确认')
    location = appointment_info.get('location', 'SuperC')
    
    subject = f"🎉 预约成功 - {location} 预约确认"
    
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
            .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
            .appointment-details {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #4CAF50; }}
            .donation-section {{ background-color: #fff3cd; padding: 15px; margin: 20px 0; border-radius: 5px; border: 1px solid #ffc107; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 0.9em; color: #777; }}
            .important-note {{ background-color: #fff3e0; padding: 15px; margin: 15px 0; border-left: 4px solid #ff9800; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 预约成功！</h1>
            </div>
            
            <div class="content">
                <p>尊敬的 {name}，</p>
                
                <p>恭喜您！您的预约已经成功完成。</p>
                
                <div class="appointment-details">
                    <h3>📅 预约详情</h3>
                    <p><strong>预约时间：</strong>{appointment_datetime}</p>
                    <p><strong>预约地点：</strong>{location}</p>
                </div>
                
                <div class="important-note">
                    <h3>⚠️ 重要提醒</h3>
                    <p>您将会收到来自官方的确认邮件，请点击邮件中的链接以最终确认您的预约。</p>
                    <p><strong>请注意检查您的邮箱（包括垃圾邮件文件夹），并在24小时内完成确认！</strong></p>
                </div>
                
                <div class="donation-section">
                    <h3>💝 支持我们的服务</h3>
                    <p>如果我们的自动预约服务帮到了您，欢迎通过以下方式支持我们：</p>
                    <ul>
                        <li><strong>支付宝/微信支付：</strong>扫描二维码打赏</li>
                        <li><strong>PayPal：</strong>paypal.me/yourpaypallink</li>
                        <li><strong>Ko-fi：</strong>ko-fi.com/yourkofilink</li>
                    </ul>
                    <p>您的支持将帮助我们继续提供和改进这项服务！🙏</p>
                </div>
                
                <p>祝您预约顺利！</p>
                
                <p>Best regards,<br>
                Aachen Termin Bot Team</p>
            </div>
            
            <div class="footer">
                <p>此邮件由系统自动发送，请勿直接回复。</p>
                <p>如有问题，请联系我们的支持团队。</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return subject, html_body


def send_notify_email(user_email: str, appointment_info: dict) -> bool:
    """
    Send notification email to user after successful appointment booking.
    
    Input types:
    - user_email: str - The email address of the user to notify
    - appointment_info: dict - Dictionary containing appointment details
      Expected keys:
      - 'name': str - Full name of the user
      - 'appointment_datetime': str - Appointment date and time
      - 'location': str - Location type (e.g., 'superc', 'infostelle')
    
    Output types:
    - bool - True if email sent successfully, False otherwise
    """
    try:
        # Get SMTP configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', '465'))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        smtp_sender = os.getenv('SMTP_SENDER', smtp_user)
        
        # Validate required configuration
        if not all([smtp_server, smtp_user, smtp_password]):
            logger.warning("SMTP 配置不完整，跳过邮件发送")
            logger.warning("请在 .env 文件中配置 SMTP_SERVER, SMTP_USER, SMTP_PASSWORD")
            return False
        
        # Validate email address
        if not user_email or '@' not in user_email:
            logger.error(f"无效的邮箱地址: {user_email}")
            return False
        
        # Generate email content
        subject, html_body = get_email_content(appointment_info)
        
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = smtp_sender
        message['To'] = user_email
        
        # Attach HTML content
        html_part = MIMEText(html_body, 'html', 'utf-8')
        message.attach(html_part)
        
        # Send email
        logger.info(f"正在向 {user_email} 发送预约确认邮件...")
        
        # Use SSL connection
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(message)
        
        logger.info(f"邮件发送成功: {user_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP 认证失败: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP 错误: {e}")
        return False
    except Exception as e:
        logger.error(f"发送邮件时发生错误: {e}", exc_info=True)
        return False
