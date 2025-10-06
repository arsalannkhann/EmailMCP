from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
from ...schemas.requests import OAuthRequest, MultiTenantEmailRequest
from ...schemas.responses import OAuthResponse, EmailAnalyticsResponse
from ...core.security import verify_api_key
from ...core.logging import log
from ...services.multi_tenant_service import MultiTenantEmailService

router = APIRouter(prefix="/v1", tags=["multi-tenant"])

# OAuth Endpoints
@router.post("/oauth/authorize", response_model=OAuthResponse)
async def initiate_oauth_flow(
    request: OAuthRequest,
    _credentials = Depends(verify_api_key)
):
    """Initiate Gmail OAuth flow for a user"""
    try:
        service = MultiTenantEmailService()
        oauth_url = await service.generate_oauth_url(
            user_id=request.user_id,
            redirect_uri=request.redirect_uri
        )
        
        log.info(f"OAuth flow initiated for user: {request.user_id}")
        return OAuthResponse(
            authorization_url=oauth_url,
            state=request.user_id
        )
    except Exception as e:
        log.error(f"OAuth initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/oauth/callback")
async def handle_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="User ID from state parameter"),
    redirect_uri: Optional[str] = Query(None, description="Redirect URI used in authorization")
):
    """Handle OAuth callback and store user tokens (public endpoint for Google redirect)"""
    try:
        service = MultiTenantEmailService()
        result = await service.process_oauth_callback(
            authorization_code=code,
            user_id=state,
            redirect_uri=redirect_uri
        )
        
        log.info(f"OAuth completed for user: {state}")
        return {
            "status": "success",
            "user_id": state,
            "email_address": result.email_address,
            "message": "Gmail account connected successfully"
        }
    except Exception as e:
        log.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/oauth/callback")
async def handle_oauth_callback_post(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="User ID from state parameter"),
    redirect_uri: Optional[str] = Query(None, description="Redirect URI used in authorization"),
    _credentials = Depends(verify_api_key)
):
    """Handle OAuth callback via POST (for frontend bridge calls)"""
    try:
        service = MultiTenantEmailService()
        result = await service.process_oauth_callback(
            authorization_code=code,
            user_id=state,
            redirect_uri=redirect_uri
        )
        
        log.info(f"OAuth completed for user: {state}")
        return {
            "status": "success",
            "user_id": state,
            "email_address": result.email_address,
            "message": "Gmail account connected successfully"
        }
    except Exception as e:
        log.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# User-specific Email Endpoints
@router.post("/users/{user_id}/messages")
async def send_user_email(
    user_id: str,
    email: MultiTenantEmailRequest,
    _credentials = Depends(verify_api_key)
):
    """Send email using user's own Gmail credentials"""
    try:
        service = MultiTenantEmailService()
        result = await service.send_user_email(user_id, email)
        
        # Log the email transaction
        await service.log_email_transaction(user_id, email, result)
        
        log.info(f"Email sent for user {user_id}: {result.message_id}")
        return result
    except Exception as e:
        log.error(f"Failed to send email for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    _credentials = Depends(verify_api_key)
):
    """Get user's email profile and connection status"""
    try:
        service = MultiTenantEmailService()
        profile = await service.get_user_profile(user_id)
        return profile
    except Exception as e:
        log.error(f"Failed to get profile for user {user_id}: {e}")
        raise HTTPException(status_code=404, detail="User profile not found")

# Reporting Endpoints
@router.get("/reports/users/{user_id}", response_model=EmailAnalyticsResponse)
async def get_user_email_report(
    user_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    _credentials = Depends(verify_api_key)
):
    """Get email analytics for a specific user"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
            
        service = MultiTenantEmailService()
        report = await service.get_user_analytics(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return report
    except Exception as e:
        log.error(f"Failed to generate report for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/summary")
async def get_platform_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    _credentials = Depends(verify_api_key)
):
    """Get platform-wide email analytics"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
            
        service = MultiTenantEmailService()
        summary = await service.get_platform_summary(start_date, end_date)
        
        return summary
    except Exception as e:
        log.error(f"Failed to generate platform summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}/gmail")
async def disconnect_user_gmail(
    user_id: str,
    _credentials = Depends(verify_api_key)
):
    """Disconnect user's Gmail account"""
    try:
        service = MultiTenantEmailService()
        await service.disconnect_user_gmail(user_id)
        
        log.info(f"Gmail disconnected for user: {user_id}")
        return {"status": "success", "message": "Gmail account disconnected"}
    except Exception as e:
        log.error(f"Failed to disconnect Gmail for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))