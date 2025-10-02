import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..schemas.requests import EmailRequest
from ..schemas.responses import EmailResponse
from ..core.config import settings
from ..core.logging import log

class SmtpClient:
    """Generic SMTP provider"""
    
    async def send(self, email: EmailRequest) -> EmailResponse:
        """Send email via SMTP"""
        try:
            if email.html:
                message = MIMEMultipart('alternative')
                message.attach(MIMEText(email.body, 'html'))
            else:
                message = MIMEText(email.body, 'plain')
            
            message['From'] = email.from_email
            message['To'] = ', '.join(email.to)
            message['Subject'] = email.subject
            
            if email.cc:
                message['Cc'] = ', '.join(email.cc)
            
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                start_tls=True
            )
            
            log.info("Email sent successfully via SMTP")
            
            return EmailResponse(
                status="success",
                provider="smtp"
            )
            
        except Exception as e:
            log.error(f"Failed to send email via SMTP: {e}")
            return EmailResponse(
                status="failed",
                provider="smtp",
                error=str(e)
            )
    
    def is_configured(self) -> bool:
        """Check if SMTP is properly configured"""
        return bool(
            settings.smtp_host and 
            settings.smtp_username and 
            settings.smtp_password
        )
