import json
import base64
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import httpx
from ..core.config import settings
from ..core.logging import log
from ..schemas.requests import EmailRequest
from ..schemas.responses import EmailResponse

class GmailAPIProvider:
    """Gmail API provider with OAuth2 refresh token support"""
    
    def __init__(self):
        self.client_id = settings.gmail_client_id
        self.client_secret = settings.gmail_client_secret
        self.refresh_token = settings.gmail_refresh_token
        self._access_token = None
        self._token_expires_at = None
        
    async def send(self, email: EmailRequest) -> EmailResponse:
        """Send email using Gmail API"""
        try:
            # Ensure we have a valid access token
            access_token = await self._get_valid_access_token()
            
            # Create the email message
            message = self._create_message(email)
            
            # Send via Gmail API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json={"raw": message}
                )
                
            if response.status_code == 200:
                result = response.json()
                log.info(f"Email sent successfully via Gmail API. Message ID: {result.get('id')}")
                return EmailResponse(
                    status="success",
                    provider="gmail_api",
                    message_id=result.get("id")
                )
            else:
                log.error(f"Gmail API error: {response.status_code} - {response.text}")
                return EmailResponse(
                    status="failed",
                    provider="gmail_api",
                    error=f"Gmail API error: {response.status_code}"
                )
                
        except Exception as e:
            log.error(f"Gmail API send error: {str(e)}")
            return EmailResponse(
                status="failed",
                provider="gmail_api",
                error=str(e)
            )
    
    async def _get_valid_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary"""
        # If we have a token and it's not expired, use it
        if self._access_token and self._token_expires_at and time.time() < self._token_expires_at:
            return self._access_token
            
        # Refresh the token
        return await self._refresh_access_token()
    
    async def _refresh_access_token(self) -> str:
        """Refresh the access token using the refresh token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": self.refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data["access_token"]
                # Gmail tokens typically expire in 1 hour
                self._token_expires_at = time.time() + token_data.get("expires_in", 3600) - 60  # 1 minute buffer
                
                log.info("Access token refreshed successfully")
                return self._access_token
            else:
                log.error(f"Token refresh failed: {response.status_code} - {response.text}")
                raise Exception(f"Token refresh failed: {response.status_code}")
                
        except Exception as e:
            log.error(f"Token refresh error: {str(e)}")
            raise
    
    def _create_message(self, email: EmailRequest) -> str:
        """Create base64 encoded email message for Gmail API"""
        if email.html:
            message = MIMEMultipart('alternative')
            message.attach(MIMEText(email.body, 'html'))
        else:
            message = MIMEText(email.body, 'plain')
            
        message['to'] = ', '.join(email.to)
        message['from'] = email.from_email
        message['subject'] = email.subject
        
        if email.cc:
            message['cc'] = ', '.join(email.cc)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return raw_message
    
    def is_configured(self) -> bool:
        """Check if Gmail API is properly configured"""
        return bool(self.client_id and self.client_secret and self.refresh_token)