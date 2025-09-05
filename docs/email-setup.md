# Email Configuration Guide

This guide explains how to configure email notifications for diary analysis results.

## Gmail Setup (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to your [Google Account settings](https://myaccount.google.com/)
2. Navigate to **Security** → **2-Step Verification**
3. Follow the instructions to enable 2FA

### Step 2: Generate App Password
1. In Google Account settings, go to **Security** → **2-Step Verification**
2. At the bottom, click **App passwords**
3. Select **Mail** and **Other (Custom name)**
4. Enter a name like "SanXing Diary Analysis"
5. Copy the generated 16-character password (keep it secure!)

### Step 3: Configure Email Settings

#### Option A: Environment Variables (Recommended)
Set these environment variables in your shell or `.env` file:

```bash
export EMAIL_SMTP_SERVER="smtp.gmail.com"
export EMAIL_SMTP_PORT="587"
export EMAIL_SENDER="your-email@gmail.com"
export EMAIL_PASSWORD="your-16-char-app-password"
export EMAIL_RECIPIENT="your-email@gmail.com"  # Can be same as sender
export EMAIL_SENDER_NAME="三省日誌分析"
```

#### Option B: Configuration File
Add to your `config.toml` file:

```toml
# Email settings
email_enabled = true
email_smtp_server = "smtp.gmail.com"
email_smtp_port = 587
email_sender = "your-email@gmail.com"
email_password = "your-16-char-app-password"
email_recipient = "your-email@gmail.com"
email_sender_name = "三省日誌分析"
email_max_retries = 2
```

## Usage Examples

### Send Email with Analysis
```bash
# Enable email for this run
python -m src.cli --spreadsheet-id YOUR_ID --creds YOUR_CREDS --email-result

# Override recipient
python -m src.cli --spreadsheet-id YOUR_ID --creds YOUR_CREDS --email-result --email-recipient "another@gmail.com"

# With config file
python -m src.cli --config config.toml --email-result
```

### Configuration Precedence
Settings are applied in this order (highest to lowest priority):
1. Command line arguments (`--email-recipient`)
2. Environment variables (`EMAIL_RECIPIENT`)
3. Configuration file (`email_recipient`)
4. Default values

## Email Content

The analysis email includes:
- **Subject**: `日誌分析報告 YYYY-MM-DD | X 篇 | Primary Theme`
- **Content**:
  - Analysis metadata (entry count, generation date)
  - Daily summaries with dates
  - Core themes with support levels
  - Hidden signals and emotional indicators
  - Anomalies (if detected)
  - Reflective question

## Other Email Providers

### Outlook/Hotmail
```bash
export EMAIL_SMTP_SERVER="smtp-mail.outlook.com"
export EMAIL_SMTP_PORT="587"
```

### Yahoo Mail
```bash
export EMAIL_SMTP_SERVER="smtp.mail.yahoo.com"
export EMAIL_SMTP_PORT="587"
```

### Custom SMTP Server
```bash
export EMAIL_SMTP_SERVER="your-smtp-server.com"
export EMAIL_SMTP_PORT="587"  # or 465 for SSL
```

## Security Best Practices

### Environment Variables
Create a `.env` file (add to `.gitignore`):
```bash
# .env file (never commit this!)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password-here
EMAIL_RECIPIENT=your-email@gmail.com
```

Load it before running:
```bash
source .env
python -m src.cli --email-result --config config.toml
```

### App Passwords vs Regular Passwords
- ✅ **Use App Passwords**: Secure, limited scope, revocable
- ❌ **Don't Use Regular Passwords**: Insecure, full account access

## Troubleshooting

### Common Issues

#### "Authentication failed" Error
- Verify your Gmail has 2FA enabled
- Double-check the app password (no spaces)
- Ensure `EMAIL_SENDER` matches the Gmail account

#### "Connection refused" Error
- Check `EMAIL_SMTP_SERVER` and `EMAIL_SMTP_PORT`
- Verify network connectivity
- Try different ports (587, 465, 25)

#### "Email not sent" Warning
- Check all required fields are set:
  - `EMAIL_SMTP_SERVER`
  - `EMAIL_SMTP_PORT`
  - `EMAIL_SENDER`
  - `EMAIL_PASSWORD`
  - `EMAIL_RECIPIENT`

### Debug Mode
Add detailed logging:
```bash
export LOG_LEVEL=DEBUG
python -m src.cli --email-result --config config.toml
```

### Test Configuration
Verify your settings work:
```bash
# Run with minimal diary data to test email
python -m src.cli --spreadsheet-id YOUR_ID --creds YOUR_CREDS --days 1 --email-result
```

## Configuration Validation

The system validates email configuration at startup. If any required field is missing, you'll see:
```
Email not configured, skipping email send
```

Required fields:
- `EMAIL_SMTP_SERVER`
- `EMAIL_SMTP_PORT` 
- `EMAIL_SENDER`
- `EMAIL_PASSWORD`
- `EMAIL_RECIPIENT`

## Sample Complete Configuration

### config.toml
```toml
# Google Sheets
spreadsheet_id = "1ABC..."  
credentials_path = "path/to/service-account.json"
tab_name = "MetaLog"

# Analysis
max_char_budget = 8000
days = 30

# Email (using environment variables for security)
email_enabled = true
email_smtp_server = "smtp.gmail.com" 
email_smtp_port = 587
email_sender_name = "我的日誌分析"
email_max_retries = 3

# Note: Sensitive fields loaded from environment
# EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT
```

### Environment Setup
```bash
# Set these in your shell profile or .env file
export EMAIL_SENDER="your-gmail@gmail.com"
export EMAIL_PASSWORD="abcd efgh ijkl mnop"  # App password format
export EMAIL_RECIPIENT="your-gmail@gmail.com"

# Run analysis with email
python -m src.cli --config config.toml --email-result
```

This setup ensures secure, reliable email delivery of your diary analysis results!