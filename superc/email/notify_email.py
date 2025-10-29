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

python3 -m superc.email.notify_email
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


def _build_base_message(subject: str, user_email: str, smtp_sender: str, html_body: str, attach_donation_images: bool = True) -> MIMEMultipart:
    """Internal helper to construct MIME email message.
    
    Input types:
    - subject: str - Email subject line
    - user_email: str - Recipient address
    - smtp_sender: str - Sender address
    - html_body: str - HTML body content
    - attach_donation_images: bool - Whether to attach donation related inline images (default True)
    
    Output types:
    - MIMEMultipart - Fully composed email message ready to send
    """
    message = MIMEMultipart('related')
    message['Subject'] = subject
    message['From'] = smtp_sender
    message['To'] = user_email

    msg_alternative = MIMEMultipart('alternative')
    html_part = MIMEText(html_body, 'html', 'utf-8')
    msg_alternative.attach(html_part)
    message.attach(msg_alternative)

    if not attach_donation_images:
        return message

    # Attach donation / reference images if available
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_specs = [
            ("wechat.png", 'wechat_qr'),
            ("pp.png", 'paypal_qr'),
            ("confirm.jpg", 'confirm_img'),
            ("code.jpg", 'code_img'),
        ]
        for filename, cid in image_specs:
            path = os.path.join(current_dir, filename)
            if not os.path.exists(path):
                logger.debug(f"Inline image not found (optional): {path}")
                continue
            with open(path, 'rb') as f:
                img_data = f.read()
            # Force jpeg subtype for .jpg files
            subtype = 'jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else None
            image_part = MIMEImage(img_data, _subtype=subtype) if subtype else MIMEImage(img_data)
            image_part.add_header('Content-ID', f'<{cid}>')
            image_part.add_header('Content-Disposition', 'inline', filename=filename)
            message.attach(image_part)
    except Exception as e:
        logger.warning(f"添加图片时发生错误(可忽略): {e}")

    return message


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
        smtp_server_env = os.getenv('SMTP_SERVER')
        smtp_user_env = os.getenv('SMTP_USER')
        smtp_password_env = os.getenv('SMTP_PASSWORD')
        smtp_sender_env = os.getenv('SMTP_SENDER')
        smtp_port = int(os.getenv('SMTP_PORT', '465'))
        # Validate presence before use to satisfy type checker
        if not smtp_server_env or not smtp_user_env or not smtp_password_env:
            logger.warning("SMTP 配置不完整，跳过邮件发送")
            return False
        smtp_server: str = smtp_server_env
        smtp_user: str = smtp_user_env
        smtp_password: str = smtp_password_env
        smtp_sender: str = smtp_sender_env or smtp_user
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
        
        # Create message (with donation images)
        message = _build_base_message(subject, user_email, smtp_sender, html_body, attach_donation_images=True)
        
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
    except Exception as e:
        logger.error(f"发送邮件时发生错误: {e}", exc_info=True)
        return False


def get_update_email_notice_content(name: str) -> tuple[str, str]:
    """Generate subject and HTML body for update-email notice.
    
    Input types:
    - name: str - User full name
    
    Output types:
    - tuple[str, str] - (subject, html_body)
    """
    display_name = name or '用户'
    subject = "📬 邮箱需要更新 - 请尽快处理"
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, 'email_update_required.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        html_body = template.format(name=display_name)
    except Exception as e:
        logger.error(f"读取邮箱更新提醒模板失败: {e}")
        html_body = f"""
        <html><body>
        <h2>邮箱需要更新</h2>
        <p>尊敬的 {display_name}，</p>
        <p>系统检测到您的邮箱存在异常，需要您登录系统更新一个新的邮箱地址，以确保后续预约通知能及时送达。</p>
        <ol>
          <li>请准备一个不同的邮箱（推荐 Gmail / Outlook 等国际邮箱）。</li>
          <li>登录预约协助系统，进入个人资料页面。</li>
          <li>更新邮箱后保存。</li>
        </ol>
        <p>完成后您将重新进入排队流程，无需重复提交信息。</p>
        <p>感谢您的配合！</p>
        </body></html>
        """
    return subject, html_body


def send_update_email_notice(user_email: str, name: str) -> bool:
    """Send an email asking the user to update their email address due to detected anomaly.
    
    Input types:
    - user_email: str - Recipient email address
    - name: str - User full name
    
    Output types:
    - bool - True if sent successfully else False
    """
    try:
        smtp_server_env = os.getenv('SMTP_SERVER')
        smtp_user_env = os.getenv('SMTP_USER')
        smtp_password_env = os.getenv('SMTP_PASSWORD')
        smtp_sender_env = os.getenv('SMTP_SENDER')
        smtp_port = int(os.getenv('SMTP_PORT', '465'))
        if not smtp_server_env or not smtp_user_env or not smtp_password_env:
            logger.warning("SMTP 配置不完整，跳过邮箱更新提醒邮件发送")
            return False
        smtp_server: str = smtp_server_env
        smtp_user: str = smtp_user_env
        smtp_password: str = smtp_password_env
        smtp_sender: str = smtp_sender_env or smtp_user
        encryption = os.getenv('SMTP_ENCRYPTION', '').strip().upper()
        timeout = float(os.getenv('SMTP_TIMEOUT', '10'))

        if not all([smtp_server, smtp_user, smtp_password]):
            logger.warning("SMTP 配置不完整，跳过邮箱更新提醒邮件发送")
            return False
        if not user_email or '@' not in user_email:
            logger.error(f"无效的邮箱地址: {user_email}")
            return False

        subject, html_body = get_update_email_notice_content(name)
        # Do not attach donation images for this transactional notice
        message = _build_base_message(subject, user_email, smtp_sender, html_body, attach_donation_images=False)

        if not encryption:
            encryption_mode = 'SSL' if smtp_port == 465 else 'STARTTLS'
        elif encryption in ('TLS', 'STARTTLS'):
            encryption_mode = 'STARTTLS'
        elif encryption in ('SSL', 'SMTPS'):
            encryption_mode = 'SSL'
        elif encryption in ('NONE', 'PLAINTEXT'):
            encryption_mode = 'NONE'
        else:
            logger.warning(f"未知的 SMTP_ENCRYPTION 值: {encryption}，将回退为 STARTTLS")
            encryption_mode = 'STARTTLS'

        logger.info(f"正在向 {user_email} 发送邮箱更新提醒邮件... (加密: {encryption_mode})")
        context = ssl.create_default_context()
        if encryption_mode == 'SSL':
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=timeout, context=context) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(message)
        elif encryption_mode == 'STARTTLS':
            with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.send_message(message)
        logger.info(f"邮箱更新提醒邮件发送成功: {user_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:  # pragma: no cover - specific branch
        logger.error(f"SMTP 认证失败(更新提醒): {e}")
        return False
    except Exception as e:  # Broad catch to ensure function returns False on any failure
        logger.error(f"发送邮箱更新提醒邮件时出现异常: {e}", exc_info=True)
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
    
    # # Send email
    send_notify_email(test_email, test_appointment_info)
    
    # Send update-email notice (示例：模拟“需要更新邮箱”场景)
    # send_update_email_notice(test_email, test_appointment_info['name'])
