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
import ssl
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
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
                    <p><strong>请注意检查您的邮箱（包括垃圾邮件文件夹），并在2小时内完成确认！</strong></p>
                </div>
                
                <div class="donation-section">
                    <h3>💝 支持我们的服务</h3>
                    <p>如果我们的自动预约服务帮到了您，欢迎通过以下方式支持我们：</p>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <div style="margin: 20px 0;">
                            <p><strong>微信打赏</strong></p>
                            <img src="cid:wechat_qr" alt="微信支付二维码" style="width: 150px; height: 150px; border: 1px solid #ddd; border-radius: 5px;">
                        </div>
                        <div style="margin: 20px 0;">
                            <p><strong>PayPal</strong></p>
                            <img src="cid:paypal_qr" alt="PayPal支付二维码" style="width: 150px; height: 150px; border: 1px solid #ddd; border-radius: 5px;">
                        </div>
                    </div>
                    
                    <p>您的支持将帮助我们继续提供和改进这项服务！🙏</p>
                </div>
                
                <p>祝您预约顺利！</p>
                
                <p>Best regards,<br>
                Aachen Termin Bot Team</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return subject, html_body


def save_email_html(appointment_info: dict, output_dir: str = "data/email_output") -> str:
    """
    Save email content as HTML file for testing purposes.
    
    Input types:
    - appointment_info: dict - Dictionary containing appointment details
    - output_dir: str - Directory to save the HTML file (default: "data/output")
    
    Output types:
    - str - Path to the saved HTML file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate email content
        subject, html_body = get_email_content(appointment_info)
        
        # For HTML preview, replace cid: references with actual file paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        wechat_path = os.path.join(current_dir, 'wechat.png')
        paypal_path = os.path.join(current_dir, 'pp.png')
        
        # Replace cid references with file paths for preview
        html_body = html_body.replace('src="cid:wechat_qr"', f'src="file://{wechat_path}"')
        html_body = html_body.replace('src="cid:paypal_qr"', f'src="file://{paypal_path}"')
        
        # Create filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        location = appointment_info.get('location', 'test').lower()
        filename = f"email_preview_{location}_{timestamp}.html"
        filepath = os.path.join(output_dir, filename)
        
        # Save HTML content to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_body)
        
        logger.info(f"邮件内容已保存到: {filepath}")
        print(f"邮件预览已保存到: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"保存邮件内容时发生错误: {e}", exc_info=True)
        return ""


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
        print("SMTP_SERVER:", smtp_server)
        print("SMTP_PORT:", smtp_port)
        print("SMTP_USER:", smtp_user)
        print("SMTP_PASSWORD:", smtp_password)
        print("SMTP_SENDER:", smtp_sender)

        # Encryption: 'SSL' (implicit TLS/SMTPS) or 'STARTTLS' (explicit TLS). 'TLS' will be treated as STARTTLS.
        encryption = os.getenv('SMTP_ENCRYPTION', '').strip().upper()
        # Timeout in seconds for network operations
        timeout = float(os.getenv('SMTP_TIMEOUT', '10'))
        
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
        message = MIMEMultipart('related')
        message['Subject'] = subject
        message['From'] = smtp_sender
        message['To'] = user_email
        
        # Create multipart alternative for HTML content
        msg_alternative = MIMEMultipart('alternative')
        
        # Attach HTML content
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg_alternative.attach(html_part)
        
        # Attach the alternative part to the main message
        message.attach(msg_alternative)
        
        # Attach QR code images
        try:
            # Get current directory (where this script is located)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Attach WeChat QR code
            wechat_path = os.path.join(current_dir, 'wechat.png')
            if os.path.exists(wechat_path):
                with open(wechat_path, 'rb') as f:
                    img_data = f.read()
                wechat_image = MIMEImage(img_data)
                wechat_image.add_header('Content-ID', '<wechat_qr>')
                wechat_image.add_header('Content-Disposition', 'inline', filename='wechat.png')
                message.attach(wechat_image)
                logger.info("微信支付二维码已添加到邮件")
            else:
                logger.warning(f"未找到微信支付二维码: {wechat_path}")
            
            # Attach PayPal QR code
            paypal_path = os.path.join(current_dir, 'pp.png')
            if os.path.exists(paypal_path):
                with open(paypal_path, 'rb') as f:
                    img_data = f.read()
                paypal_image = MIMEImage(img_data)
                paypal_image.add_header('Content-ID', '<paypal_qr>')
                paypal_image.add_header('Content-Disposition', 'inline', filename='pp.png')
                message.attach(paypal_image)
                logger.info("PayPal支付二维码已添加到邮件")
            else:
                logger.warning(f"未找到PayPal支付二维码: {paypal_path}")
                
        except Exception as e:
            logger.warning(f"添加支付二维码时发生错误: {e}")
            # Continue sending email without images
        
        # Determine encryption method
        # Heuristics if not explicitly set
        if not encryption:
            if smtp_port == 465:
                encryption_mode = 'SSL'
            else:
                # Default to STARTTLS for common ports like 587/25 when unspecified
                encryption_mode = 'STARTTLS'
        elif encryption in ('TLS', 'STARTTLS'):
            encryption_mode = 'STARTTLS'
        elif encryption in ('SSL', 'SMTPS'):
            encryption_mode = 'SSL'
        elif encryption in ('NONE', 'PLAINTEXT'):
            encryption_mode = 'NONE'
        else:
            logger.warning(f"未知的 SMTP_ENCRYPTION 值: {encryption}，将回退为 STARTTLS")
            encryption_mode = 'STARTTLS'

        logger.info(f"正在向 {user_email} 发送预约确认邮件... (加密: {encryption_mode}, 服务器: {smtp_server}:{smtp_port})")

        # Create secure default SSL context
        context = ssl.create_default_context()

        # Send email with the chosen encryption method
        if encryption_mode == 'SSL':
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=timeout, context=context) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(message)
        elif encryption_mode == 'STARTTLS':
            with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                # Be explicit with EHLO for better compatibility
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.send_message(message)
        else:  # NONE (not recommended, but offered for special/dev scenarios)
            with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                server.ehlo()
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

if __name__ == "__main__":
    # Test email sending
    test_appointment_info = {
        'name': '测试用户',
        'appointment_datetime': '2024-10-15 10:00',
        'location': 'SuperC'
    }
    test_email = 'hanbin.9797@gmail.com'
    
    # Save email content as HTML for testing
    html_file_path = save_email_html(test_appointment_info)
    
    # Send email
    send_notify_email(test_email, test_appointment_info)
