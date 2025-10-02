import uuid
from typing import Optional
from ..schemas.requests import EmailRequest
from ..schemas.responses import EmailResponse
from ..providers.base import EmailProvider
from ..core.logging import log

class EmailService:
    """Core email sending business logic"""
    
    def __init__(self, provider: EmailProvider):
        self.provider = provider
    
    async def send_email(
        self,
        email: EmailRequest,
        request_id: Optional[str] = None
    ) -> EmailResponse:
        """Send email through configured provider"""
        if not request_id:
            request_id = str(uuid.uuid4())
        
        log.bind(request_id=request_id).info(
            f"Processing email: provider={email.provider}, to={email.to}"
        )
        
        try:
            response = await self.provider.send(email)
            
            log.bind(request_id=request_id).info(
                f"Email send completed: status={response.status}"
            )
            
            return response
            
        except Exception as e:
            log.bind(request_id=request_id).error(f"Email send failed: {e}")
            return EmailResponse(
                status="failed",
                provider=email.provider,
                error=str(e)
            )
