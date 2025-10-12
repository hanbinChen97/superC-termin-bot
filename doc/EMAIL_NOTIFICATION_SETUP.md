# Email Notification Configuration Guide

## Overview
The email notification feature automatically sends a confirmation email to users after successful appointment booking. The email includes:
- Appointment details (date, time, location)
- Important reminder to confirm via official email
- Donation/support information to encourage contributions

## Setup Instructions

### 1. Configure SMTP Settings

Create a `.env` file in the project root (or update your existing one) with the following SMTP configuration:

```bash
# SMTP Email Configuration
SMTP_SERVER=smtp.example.com
SMTP_PORT=465
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_email_password
SMTP_SENDER=your_email@example.com
```

### 2. Common SMTP Providers

#### Gmail
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # Use App Password, not regular password
SMTP_SENDER=your_email@gmail.com
```

**Note:** For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an App Password at https://myaccount.google.com/apppasswords
3. Use the App Password (not your regular Gmail password)

#### Outlook/Office 365
```bash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your_email@outlook.com
SMTP_PASSWORD=your_password
SMTP_SENDER=your_email@outlook.com
```

#### QQ Mail (腾讯QQ邮箱)
```bash
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your_email@qq.com
SMTP_PASSWORD=your_authorization_code  # Use authorization code, not password
SMTP_SENDER=your_email@qq.com
```

**Note:** For QQ Mail:
1. Enable SMTP service in settings
2. Generate an authorization code
3. Use the authorization code (not your QQ password)

#### 163 Mail (网易163邮箱)
```bash
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
SMTP_USER=your_email@163.com
SMTP_PASSWORD=your_authorization_code  # Use authorization code, not password
SMTP_SENDER=your_email@163.com
```

### 3. Test Email Configuration

You can test the email configuration by running the unit tests:

```bash
source .venv/bin/activate
python -m unittest tests.test_notify_email -v
```

### 4. Behavior

- **Success Case:** When email is sent successfully, you'll see:
  ```
  INFO - 已向用户 user@example.com 发送预约确认邮件
  ```

- **Configuration Missing:** If SMTP is not configured, the bot will:
  - Log a warning message
  - Continue processing (booking is not affected)
  - Skip email sending

- **Email Failure:** If email sending fails, the bot will:
  - Log an error message
  - Continue processing (booking is not affected)
  - The appointment is still successfully booked in the database

### 5. Customize Email Content

To customize the email template, edit `superc/notify_email.py`:

1. Update the `get_email_content()` function
2. Modify the HTML template
3. Add your donation links (PayPal, Ko-fi, etc.)

Example areas to customize:
- Donation links and QR codes
- Email styling (colors, fonts)
- Additional appointment information
- Contact information

## Security Best Practices

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use App Passwords** - Don't use your main email password
3. **Limit permissions** - Use email accounts with minimal permissions
4. **Rotate credentials** - Change passwords periodically
5. **Monitor logs** - Check for failed authentication attempts

## Troubleshooting

### Email not being sent
1. Check SMTP configuration in `.env` file
2. Verify credentials are correct
3. Check firewall/network settings
4. Review logs for specific error messages

### Authentication failures
1. Ensure you're using App Password (not regular password) for Gmail
2. Verify authorization code for QQ/163 mail
3. Check if SMTP access is enabled in email provider settings

### Connection timeouts
1. Verify SMTP_SERVER and SMTP_PORT are correct
2. Check if port 465 or 587 is blocked by firewall
3. Try alternative port (465 for SSL, 587 for TLS)

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review error messages in console output
3. Ensure database connection is working
4. Open an issue on GitHub with relevant log excerpts
