"""Email service for sending diary analysis results"""

import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional, Dict, Any
from datetime import datetime
import json

try:
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

from .models import InsightPack
from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class EmailService:
    """Handles sending analysis results via email using SMTP"""

    def __init__(self, config: Config):
        self.config = config
        self.gmail_service = None

    def send_analysis_result(self, insight_pack: InsightPack, run_id: str) -> bool:
        """
        Send diary analysis results via email
        
        Args:
            insight_pack: Analysis results to send
            run_id: Run identifier for tracking
            
        Returns:
            bool: Success status
        """
        if not self._validate_email_config():
            logger.warning("Email not configured, skipping email send")
            return False

        try:
            subject = self._build_subject(insight_pack)
            html_body = self._build_html_body(insight_pack)
            
            success = self._send_email(
                recipient=self.config.EMAIL_RECIPIENT,
                subject=subject,
                html_body=html_body,
                run_id=run_id
            )
            
            if success:
                logger.info("Analysis email sent successfully to %s", self.config.EMAIL_RECIPIENT)
                
                # Apply Gmail label if enabled
                if getattr(self.config, 'EMAIL_APPLY_LABEL', True):
                    try:
                        self._apply_gmail_label(subject, self.config.EMAIL_RECIPIENT)
                    except Exception as e:
                        logger.warning("Gmail labeling failed (email still sent): %s", str(e))
                        logger.info("💡 Tip: Create Gmail filter - From: %s, Subject: '日誌分析報告', Label: 'Meta-Awareness/Weekly'", 
                                  self.config.EMAIL_SENDER)
            else:
                logger.error("Failed to send analysis email")
                
            return success
            
        except Exception as e:
            logger.error("Email sending failed: %s", str(e))
            return False

    def _validate_email_config(self) -> bool:
        """Validate email configuration is complete"""
        required_fields = [
            'EMAIL_SMTP_SERVER',
            'EMAIL_SMTP_PORT', 
            'EMAIL_SENDER',
            'EMAIL_PASSWORD',
            'EMAIL_RECIPIENT'
        ]
        
        missing_fields = []
        for field in required_fields:
            value = getattr(self.config, field, None)
            if not value:
                missing_fields.append(field)
                logger.debug("Missing email config field: %s (value: %s)", field, value)
        
        if missing_fields:
            logger.warning("Email config incomplete. Missing fields: %s", missing_fields)
            return False
            
        logger.debug("Email config validation passed")
        return True

    def _send_email(self, recipient: str, subject: str, html_body: str, run_id: str) -> bool:
        """Send email via SMTP with retry logic"""
        max_retries = getattr(self.config, 'EMAIL_MAX_RETRIES', 2)
        
        for attempt in range(max_retries):
            try:
                # Create message
                message = MIMEMultipart("alternative")
                message["Subject"] = subject
                message["From"] = formataddr((
                    getattr(self.config, 'EMAIL_SENDER_NAME', '三省日誌分析'),
                    self.config.EMAIL_SENDER
                ))
                message["To"] = recipient
                message["X-Run-ID"] = run_id

                # Add HTML content
                html_part = MIMEText(html_body, "html", "utf-8")
                message.attach(html_part)

                # Send via SMTP
                context = ssl.create_default_context()
                
                with smtplib.SMTP(self.config.EMAIL_SMTP_SERVER, self.config.EMAIL_SMTP_PORT) as server:
                    server.starttls(context=context)
                    server.login(self.config.EMAIL_SENDER, self.config.EMAIL_PASSWORD)
                    server.send_message(message)
                
                logger.info("Email sent successfully on attempt %d", attempt + 1)
                return True
                
            except Exception as e:
                logger.warning("Email attempt %d failed: %s", attempt + 1, str(e))
                if attempt == max_retries - 1:
                    logger.error("All email attempts failed")
                    return False
        
        return False

    def _build_subject(self, insight_pack: InsightPack) -> str:
        """Build email subject from analysis data"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        entry_count = insight_pack.meta.get("entriesAnalyzed", 0)
        
        # Try to get primary theme if available
        primary_theme = ""
        if insight_pack.themes:
            primary_theme = f" | {insight_pack.themes[0].label}"
        
        return f"日誌分析報告 {date_str} | {entry_count} 篇{primary_theme}"

    def _build_html_body(self, insight_pack: InsightPack) -> str:
        """Build HTML email body from analysis results"""
        # Generate HTML content
        analysis_html = self._render_analysis_html(insight_pack)
        
        # CSS styles for email
        css_styles = """
        <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #34495e;
            max-width: 680px;
            margin: 20px auto;
            padding: 0;
            background-color: #f8f9fa;
        }
        .container {
            background-color: #fff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 24px;
        }
        .meta-info {
            color: #6c757d;
            font-size: 14px;
            margin-top: 10px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section-title {
            color: #2980b9;
            font-size: 18px;
            margin-bottom: 15px;
            padding-left: 12px;
            border-left: 4px solid #3498db;
            font-weight: 600;
        }
        .daily-summaries {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .daily-item {
            margin-bottom: 12px;
            padding: 10px;
            background-color: #fff;
            border-radius: 6px;
            border-left: 3px solid #3498db;
        }
        .daily-date {
            font-weight: 600;
            color: #2c3e50;
            font-size: 14px;
        }
        .daily-summary {
            margin-top: 5px;
            color: #495057;
        }
        .themes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .theme-item {
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #bee5eb;
        }
        .theme-label {
            font-weight: 600;
            color: #0056b3;
            font-size: 16px;
            margin-bottom: 5px;
        }
        .theme-support {
            color: #6c757d;
            font-size: 14px;
        }
        .reflection-box {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
            margin-top: 15px;
        }
        .reflection-question {
            color: #856404;
            font-size: 16px;
            font-weight: 500;
            font-style: italic;
            text-align: center;
        }
        .insights-list {
            list-style: none;
            padding: 0;
        }
        .insights-list li {
            background-color: #f8f9fa;
            margin-bottom: 10px;
            padding: 12px 15px;
            border-radius: 6px;
            border-left: 3px solid #28a745;
            position: relative;
        }
        .insights-list li::before {
            content: '•';
            color: #28a745;
            margin-right: 10px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }
        .run-info {
            background-color: #f1f3f4;
            padding: 10px 15px;
            border-radius: 6px;
            margin-top: 15px;
            font-size: 12px;
            color: #5f6368;
        }
        </style>
        """
        
        return f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>日誌分析報告</title>
            {css_styles}
        </head>
        <body>
            <div class="container">
                {analysis_html}
            </div>
        </body>
        </html>
        """

    def _render_analysis_html(self, insight_pack: InsightPack) -> str:
        """Render InsightPack to HTML"""
        # Header section
        run_id = insight_pack.meta.get("run_id", "unknown")
        entry_count = insight_pack.meta.get("entriesAnalyzed", 0)
        generated_at = insight_pack.meta.get("generatedAt", "")
        
        html_parts = [
            '<div class="header">',
            '<h1>日誌分析報告</h1>',
            f'<div class="meta-info">分析了 {entry_count} 篇日誌 · {generated_at[:10] if generated_at else ""}</div>',
            '</div>'
        ]
        
        # Daily summaries section
        if insight_pack.dailySummaries:
            html_parts.extend([
                '<div class="section">',
                '<h2 class="section-title">每日摘要</h2>',
                '<div class="daily-summaries">'
            ])
            
            for summary in insight_pack.dailySummaries:
                html_parts.extend([
                    '<div class="daily-item">',
                    f'<div class="daily-date">{summary.date}</div>',
                    f'<div class="daily-summary">{self._escape_html(summary.summary)}</div>',
                    '</div>'
                ])
            
            html_parts.extend(['</div>', '</div>'])
        
        # Themes section
        if insight_pack.themes:
            html_parts.extend([
                '<div class="section">',
                '<h2 class="section-title">核心主題</h2>',
                '<div class="themes-grid">'
            ])
            
            for theme in insight_pack.themes:
                html_parts.extend([
                    '<div class="theme-item">',
                    f'<div class="theme-label">{self._escape_html(theme.label)}</div>',
                    f'<div class="theme-support">支持度: {theme.support}</div>',
                    '</div>'
                ])
            
            html_parts.extend(['</div>', '</div>'])
        
        # Hidden signals section
        if insight_pack.hiddenSignals:
            html_parts.extend([
                '<div class="section">',
                '<h2 class="section-title">潛在信號</h2>',
                '<ul class="insights-list">'
            ])
            
            for signal in insight_pack.hiddenSignals:
                html_parts.append(f'<li>{self._escape_html(signal)}</li>')
            
            html_parts.extend(['</ul>', '</div>'])
        
        # Emotional indicators section
        if insight_pack.emotionalIndicators:
            html_parts.extend([
                '<div class="section">',
                '<h2 class="section-title">情緒指標</h2>',
                '<ul class="insights-list">'
            ])
            
            for indicator in insight_pack.emotionalIndicators:
                html_parts.append(f'<li>{self._escape_html(str(indicator))}</li>')
            
            html_parts.extend(['</ul>', '</div>'])
        
        # Anomalies section
        if insight_pack.anomalies:
            html_parts.extend([
                '<div class="section">',
                '<h2 class="section-title">異常觀察</h2>',
                '<ul class="insights-list">'
            ])
            
            for anomaly in insight_pack.anomalies:
                html_parts.append(f'<li>{self._escape_html(anomaly)}</li>')
            
            html_parts.extend(['</ul>', '</div>'])
        
        # Reflection question section
        if insight_pack.reflectiveQuestion:
            html_parts.extend([
                '<div class="section">',
                '<h2 class="section-title">反思問題</h2>',
                '<div class="reflection-box">',
                f'<div class="reflection-question">{self._escape_html(insight_pack.reflectiveQuestion)}</div>',
                '</div>',
                '</div>'
            ])
        
        # Footer
        html_parts.extend([
            '<div class="footer">',
            '<div>三省日誌分析引擎 · 用心記錄，智慧成長</div>',
            f'<div class="run-info">Run ID: {run_id}</div>',
            '</div>'
        ])
        
        return ''.join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not isinstance(text, str):
            text = str(text)
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))

    def _init_gmail_service(self):
        """Initialize Gmail API service using service account credentials"""
        if not GMAIL_API_AVAILABLE:
            logger.debug("Gmail API not available (missing google-api-python-client)")
            return None
            
        if not hasattr(self.config, 'CREDENTIALS_PATH') or not self.config.CREDENTIALS_PATH:
            logger.debug("No credentials path for Gmail API")
            return None
            
        try:
            # Use the same service account as the Sheets API
            credentials = Credentials.from_service_account_file(
                str(self.config.CREDENTIALS_PATH),
                scopes=['https://www.googleapis.com/auth/gmail.modify']
            )
            
            # Delegate to the user's email (impersonate)
            if hasattr(credentials, 'with_subject'):
                delegated_credentials = credentials.with_subject(self.config.EMAIL_SENDER)
                service = build('gmail', 'v1', credentials=delegated_credentials)
            else:
                logger.warning("Cannot delegate Gmail API access - labels will not work")
                return None
                
            logger.debug("Gmail API service initialized successfully")
            return service
            
        except Exception as e:
            logger.debug("Failed to initialize Gmail API: %s", str(e))
            return None

    def _apply_gmail_label(self, subject: str, recipient: str):
        """Apply Gmail label to sent email"""
        if not self.gmail_service:
            self.gmail_service = self._init_gmail_service()
            
        if not self.gmail_service:
            logger.debug("Gmail labeling skipped - API not available")
            return
            
        try:
            # Wait a moment for email to be indexed
            time.sleep(3)
            
            # Search for the sent email
            query = f'to:{recipient} subject:"{subject}" from:me newer_than:5m'
            logger.debug("Searching Gmail with query: %s", query)
            
            search_result = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=1
            ).execute()
            
            messages = search_result.get('messages', [])
            if not messages:
                logger.warning("Could not find sent email for labeling")
                return
                
            message_id = messages[0]['id']
            
            # Get or create the label
            label_name = getattr(self.config, 'EMAIL_GMAIL_LABEL', 'Meta-Awareness/Weekly')
            label_id = self._get_or_create_label(label_name)
            
            if label_id:
                # Apply the label
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'addLabelIds': [label_id]}
                ).execute()
                
                logger.info("Gmail label '%s' applied successfully", label_name)
            else:
                logger.warning("Could not create Gmail label")
                
        except Exception as e:
            logger.warning("Failed to apply Gmail label: %s", str(e))

    def _get_or_create_label(self, label_name: str) -> Optional[str]:
        """Get existing label or create new one"""
        try:
            # List existing labels
            labels_result = self.gmail_service.users().labels().list(userId='me').execute()
            labels = labels_result.get('labels', [])
            
            # Check if label already exists
            for label in labels:
                if label['name'] == label_name:
                    logger.debug("Found existing Gmail label: %s", label_name)
                    return label['id']
            
            # Create new label
            logger.debug("Creating new Gmail label: %s", label_name)
            label_body = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            created_label = self.gmail_service.users().labels().create(
                userId='me',
                body=label_body
            ).execute()
            
            logger.info("Created Gmail label: %s", label_name)
            return created_label['id']
            
        except Exception as e:
            logger.warning("Failed to get/create Gmail label: %s", str(e))
            return None