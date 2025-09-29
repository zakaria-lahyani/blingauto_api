"""
Email Service for sending emails with various providers
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import aiofiles
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl
from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger(__name__)


@dataclass
class EmailTemplate:
    """Email template data"""
    subject: str
    html_body: str
    text_body: Optional[str] = None
    attachments: Optional[List[str]] = None


@dataclass
class EmailData:
    """Email sending data"""
    to: str
    subject: str
    html_body: str
    text_body: Optional[str] = None
    attachments: Optional[List[str]] = None
    from_email: Optional[str] = None


class EmailProvider(ABC):
    """Abstract email provider interface"""
    
    @abstractmethod
    async def send_email(self, email_data: EmailData) -> bool:
        """Send an email"""
        pass
    
    @abstractmethod
    async def send_bulk_email(self, emails: List[EmailData]) -> Dict[str, bool]:
        """Send multiple emails"""
        pass


class SMTPEmailProvider(EmailProvider):
    """SMTP email provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.host = config.get("smtp_host", "localhost")
        self.port = config.get("smtp_port", 587)
        self.username = config.get("smtp_username")
        self.password = config.get("smtp_password")
        self.use_tls = config.get("smtp_use_tls", True)
        self.default_from = config.get("from_email", "noreply@carwash.com")
    
    async def send_email(self, email_data: EmailData) -> bool:
        """Send email via SMTP"""
        try:
            # Run in thread pool to avoid blocking
            return await asyncio.get_event_loop().run_in_executor(
                None, self._send_email_sync, email_data
            )
        except Exception as e:
            logger.error(f"Failed to send email to {email_data.to}: {e}")
            return False
    
    def _send_email_sync(self, email_data: EmailData) -> bool:
        """Synchronous email sending"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email_data.subject
            msg['From'] = email_data.from_email or self.default_from
            msg['To'] = email_data.to
            
            # Add text and HTML parts
            if email_data.text_body:
                text_part = MIMEText(email_data.text_body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            html_part = MIMEText(email_data.html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add attachments if any
            if email_data.attachments:
                for attachment_path in email_data.attachments:
                    self._add_attachment(msg, attachment_path)
            
            # Create SMTP connection
            if self.use_tls:
                context = ssl.create_default_context()
                server = smtplib.SMTP(self.host, self.port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP(self.host, self.port)
            
            # Login if credentials provided
            if self.username and self.password:
                server.login(self.username, self.password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {email_data.to}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error sending to {email_data.to}: {e}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add file attachment to email"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {Path(file_path).name}'
            )
            msg.attach(part)
        except Exception as e:
            logger.error(f"Failed to add attachment {file_path}: {e}")
    
    async def send_bulk_email(self, emails: List[EmailData]) -> Dict[str, bool]:
        """Send multiple emails"""
        results = {}
        for email_data in emails:
            results[email_data.to] = await self.send_email(email_data)
        return results


class MockEmailProvider(EmailProvider):
    """Mock email provider for testing/development"""
    
    def __init__(self, config: Dict[str, Any]):
        self.sent_emails = []
        self.default_from = config.get("from_email", "noreply@carwash.com")
    
    async def send_email(self, email_data: EmailData) -> bool:
        """Mock email sending - just log and store"""
        try:
            # Store for testing
            self.sent_emails.append({
                "to": email_data.to,
                "subject": email_data.subject,
                "html_body": email_data.html_body,
                "text_body": email_data.text_body,
                "from_email": email_data.from_email or self.default_from,
                "sent_at": asyncio.get_event_loop().time()
            })
            
            logger.info(f"[MOCK EMAIL] To: {email_data.to}, Subject: {email_data.subject}")
            logger.debug(f"[MOCK EMAIL] Body: {email_data.html_body[:200]}...")
            
            return True
        except Exception as e:
            logger.error(f"Mock email error: {e}")
            return False
    
    async def send_bulk_email(self, emails: List[EmailData]) -> Dict[str, bool]:
        """Send multiple mock emails"""
        results = {}
        for email_data in emails:
            results[email_data.to] = await self.send_email(email_data)
        return results
    
    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Get all sent emails (for testing)"""
        return self.sent_emails
    
    def clear_sent_emails(self):
        """Clear sent emails list"""
        self.sent_emails.clear()


class EmailService:
    """Main email service with template support"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = self._create_provider()
        self.template_env = self._setup_templates()
        
    def _create_provider(self) -> EmailProvider:
        """Create email provider based on configuration"""
        provider_type = self.config.get("email_provider", "mock").lower()
        
        if provider_type == "smtp":
            return SMTPEmailProvider(self.config)
        elif provider_type == "mock":
            return MockEmailProvider(self.config)
        else:
            logger.warning(f"Unknown email provider '{provider_type}', using mock")
            return MockEmailProvider(self.config)
    
    def _setup_templates(self) -> Environment:
        """Setup Jinja2 template environment"""
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        
        return Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
    
    async def send_email(
        self, 
        to: str, 
        subject: str, 
        html_body: str, 
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Send a single email"""
        email_data = EmailData(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=from_email,
            attachments=attachments
        )
        
        return await self.provider.send_email(email_data)
    
    async def send_template_email(
        self,
        to: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Send email using a template"""
        try:
            # Load and render template
            template = self.template_env.get_template(f"{template_name}.html")
            html_body = template.render(**context)
            
            # Try to load text version
            text_body = None
            try:
                text_template = self.template_env.get_template(f"{template_name}.txt")
                text_body = text_template.render(**context)
            except:
                # Text template is optional
                pass
            
            # Get subject from context or use default
            subject = context.get("subject", f"Notification from Car Wash Service")
            
            return await self.send_email(
                to=to,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                from_email=from_email,
                attachments=attachments
            )
            
        except Exception as e:
            logger.error(f"Failed to send template email '{template_name}' to {to}: {e}")
            return False
    
    async def send_verification_email(
        self, 
        to: str, 
        first_name: str, 
        verification_link: str,
        expires_hours: int = 24
    ) -> bool:
        """Send email verification email"""
        context = {
            "subject": "Verify Your Email - Car Wash Service",
            "first_name": first_name,
            "verification_link": verification_link,
            "expires_hours": expires_hours,
            "app_name": "Car Wash Service",
            "support_email": self.config.get("support_email", "support@carwash.com")
        }
        
        return await self.send_template_email(
            to=to,
            template_name="email_verification",
            context=context
        )
    
    async def send_password_reset_email(
        self, 
        to: str, 
        first_name: str, 
        reset_link: str,
        expires_hours: int = 2
    ) -> bool:
        """Send password reset email"""
        context = {
            "subject": "Reset Your Password - Car Wash Service",
            "first_name": first_name,
            "reset_link": reset_link,
            "expires_hours": expires_hours,
            "app_name": "Car Wash Service",
            "support_email": self.config.get("support_email", "support@carwash.com")
        }
        
        return await self.send_template_email(
            to=to,
            template_name="password_reset",
            context=context
        )
    
    async def send_welcome_email(
        self, 
        to: str, 
        first_name: str,
        login_link: Optional[str] = None
    ) -> bool:
        """Send welcome email after email verification"""
        context = {
            "subject": "Welcome to Car Wash Service!",
            "first_name": first_name,
            "login_link": login_link or self.config.get("app_url", "https://carwash.com"),
            "app_name": "Car Wash Service",
            "support_email": self.config.get("support_email", "support@carwash.com")
        }
        
        return await self.send_template_email(
            to=to,
            template_name="welcome",
            context=context
        )
    
    async def send_bulk_emails(self, emails: List[EmailData]) -> Dict[str, bool]:
        """Send multiple emails"""
        return await self.provider.send_bulk_email(emails)
    
    def get_provider(self) -> EmailProvider:
        """Get the current email provider (useful for testing)"""
        return self.provider


# Global email service instance
_email_service: Optional[EmailService] = None


def init_email_service(config: Dict[str, Any]) -> EmailService:
    """Initialize global email service"""
    global _email_service
    _email_service = EmailService(config)
    return _email_service


def get_email_service() -> EmailService:
    """Get global email service instance"""
    global _email_service
    if _email_service is None:
        # Auto-initialize with default mock config for development
        logger.warning("Email service not initialized, using default mock configuration")
        default_config = {
            "email_provider": "mock",
            "from_email": "noreply@carwash.com"
        }
        _email_service = EmailService(default_config)
    return _email_service