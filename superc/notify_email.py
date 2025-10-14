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

python3 superc/notify_email.py
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
    
    # Read HTML template from file
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, 'email_template.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
        
        # Format the template with appointment information
        html_body = html_template.format(
            name=name,
            appointment_datetime=appointment_datetime,
            location=location
        )
        
    except Exception as e:
        logger.error(f"读取邮件模板文件时发生错误: {e}")
        # Fallback to a simple HTML content if template reading fails
        html_body = f"""
        <html>
        <body>
            <h1>🎉 预约成功！</h1>
            <p>尊敬的 {name}，</p>
            <p>恭喜您！您的预约已经成功完成。</p>
            <p><strong>预约时间：</strong>{appointment_datetime}</p>
            <p><strong>预约地点：</strong>{location}</p>
            <p>请注意检查您的邮箱（包括垃圾邮件文件夹），并在2小时内完成确认！</p>
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
        confirm_path = os.path.join(current_dir, 'confirm.jpg')
        code_path = os.path.join(current_dir, 'code.jpg')
        
        # Replace cid references with file paths for preview
        html_body = html_body.replace('src="cid:wechat_qr"', f'src="file://{wechat_path}"')
        html_body = html_body.replace('src="cid:paypal_qr"', f'src="file://{paypal_path}"')
        html_body = html_body.replace('src="cid:confirm_img"', f'src="file://{confirm_path}"')
        html_body = html_body.replace('src="cid:code_img"', f'src="file://{code_path}"')
        
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
        # print("SMTP_PASSWORD:", smtp_password)
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
            
            # Attach confirm.jpg image (force subtype)
            confirm_path = os.path.join(current_dir, 'confirm.jpg')
            if os.path.exists(confirm_path):
                with open(confirm_path, 'rb') as f:
                    img_data = f.read()
                confirm_image = MIMEImage(img_data, _subtype='jpeg')
                confirm_image.add_header('Content-ID', '<confirm_img>')
                confirm_image.add_header('Content-Disposition', 'inline', filename='confirm.jpg')
                message.attach(confirm_image)
                logger.info("确认邮件示例图片已添加到邮件: confirm.jpg")
            else:
                logger.warning(f"未找到确认邮件示例图片: confirm.jpg")

            # Attach code.jpg image (force subtype)
            code_path = os.path.join(current_dir, 'code.jpg')
            if os.path.exists(code_path):
                with open(code_path, 'rb') as f:
                    img_data = f.read()
                code_image = MIMEImage(img_data, _subtype='jpeg')
                code_image.add_header('Content-ID', '<code_img>')
                code_image.add_header('Content-Disposition', 'inline', filename='code.jpg')
                message.attach(code_image)
                logger.info("确认码示例图片已添加到邮件: code.jpg")
            else:
                logger.warning(f"未找到确认码示例图片: code.jpg")
                
        except Exception as e:
            logger.warning(f"添加图片时发生错误: {e}")
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
