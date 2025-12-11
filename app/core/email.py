"""
Email service with Jinja2 template engine.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional, Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings


# Setup Jinja2 environment
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml'])
)


class EmailService:
    """Service for sending emails via SMTP with Jinja2 templates."""
    
    @staticmethod
    def render_template(template_name: str, context: Dict[str, Any]) -> str:
        """
        Render an email template with context.
        
        Args:
            template_name: Name of the template file (e.g., 'otp.html')
            context: Dictionary of variables to pass to the template
            
        Returns:
            Rendered HTML string
        """
        template = jinja_env.get_template(template_name)
        return template.render(**context)
    
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text fallback (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        # If email is disabled, just log to console
        if not settings.EMAIL_ENABLED:
            print(f"\n{'='*60}")
            print(f"📧 EMAIL (Console Mode - EMAIL_ENABLED=False)")
            print(f"{'='*60}")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"\n{text_content or 'See HTML content above'}")
            print(f"{'='*60}\n")
            return True
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            message["To"] = to_email
            
            # Add text and HTML parts
            if text_content:
                message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_otp_email(email: str, otp: str, purpose: str = "email verification") -> bool:
        """
        Send OTP email for verification using Jinja2 template.
        
        Args:
            email: Recipient email
            otp: 6-digit OTP code
            purpose: Purpose of OTP (e.g., "email verification", "password reset")
            
        Returns:
            True if sent successfully
        """
        subject = f"Your {purpose.title()} Code"
        
        # Render HTML template
        html_content = EmailService.render_template('otp.html', {
            'otp': otp,
            'purpose': purpose,
            'app_name': settings.PROJECT_NAME
        })
        
        # Plain text fallback
        text_content = f"""
Verification Code for {purpose.title()}

Your verification code is: {otp}

This code is valid for 10 minutes.

If you didn't request this code, please ignore this email.

© 2024 {settings.PROJECT_NAME}
        """.strip()
        
        return await EmailService.send_email(email, subject, html_content, text_content)
    
    @staticmethod
    async def send_password_reset_email(email: str, otp: str) -> bool:
        """
        Send password reset email with OTP.
        
        Args:
            email: Recipient email
            otp: 6-digit OTP code
            
        Returns:
            True if sent successfully
        """
        return await EmailService.send_otp_email(email, otp, "password reset")
    
    @staticmethod
    async def send_welcome_email(email: str, name: str) -> bool:
        """
        Send welcome email after successful registration using Jinja2 template.
        
        Args:
            email: Recipient email
            name: User's name
            
        Returns:
            True if sent successfully
        """
        subject = f"Welcome to {settings.PROJECT_NAME}!"
        
        # Render HTML template
        html_content = EmailService.render_template('welcome.html', {
            'name': name,
            'app_name': settings.PROJECT_NAME,
            'frontend_url': settings.FRONTEND_URL
        })
        
        # Plain text fallback
        text_content = f"""
Welcome to {settings.PROJECT_NAME}!

Hi {name},

Your account has been successfully verified and is ready to use.

Get started: {settings.FRONTEND_URL}/login

© 2024 {settings.PROJECT_NAME}
        """.strip()
        
        return await EmailService.send_email(email, subject, html_content, text_content)
