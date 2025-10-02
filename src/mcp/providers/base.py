from typing import Protocol
from ..schemas.requests import EmailRequest
from ..schemas.responses import EmailResponse

class EmailProvider(Protocol):
    """Abstract protocol for email providers"""
    
    async def send(self, email: EmailRequest) -> EmailResponse:
        """Send an email and return response"""
        ...
    
    def is_configured(self) -> bool:
        """Check if the provider is properly configured"""
        ...
