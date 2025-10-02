from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
import uuid
from ...schemas.requests import EmailRequest
from ...schemas.responses import EmailResponse, ErrorDetail
from ...services.email_service import EmailService
from ...providers.factory import get_email_provider as get_provider
from ...core.security import verify_api_key
from ...core.logging import log

router = APIRouter(prefix="/v1", tags=["messages"])

async def get_email_service(email: EmailRequest) -> EmailService:
    """Factory function to return the correct email service"""
    try:
        # Use the provider factory to get the appropriate provider
        provider = get_provider(email.provider if email.provider != "auto" else None)
        return EmailService(provider)
    except Exception as e:
        log.error(f"Failed to create email provider: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize email provider: {str(e)}"
        )

@router.post(
    "/messages",
    response_model=EmailResponse,
    status_code=200,
    summary="Send an email"
)
async def send_email(
    email: EmailRequest,
    x_request_id: Optional[str] = Header(None),
    api_key: str = Depends(verify_api_key),
    email_service: EmailService = Depends(get_email_service)
):
    """Send an email through the MCP service"""
    request_id = x_request_id or str(uuid.uuid4())
    
    log.bind(request_id=request_id).info(
        f"Received request: provider={email.provider}"
    )
    
    try:
        response = await email_service.send_email(email, request_id)
        return response
    except Exception as e:
        log.bind(request_id=request_id).error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-service",
        "version": "0.1.0"
    }
