from typing import Dict, Any
from .gmail_api import GmailAPIProvider
from ..services.aws_secrets import AWSSecretsManager
from ..core.config import settings
from ..core.logging import log
from ..schemas.requests import EmailRequest
from ..schemas.responses import EmailResponse

class GmailAPIProductionProvider(GmailAPIProvider):
    """Production Gmail API provider with AWS Secrets Manager integration"""
    
    def __init__(self):
        self.settings = settings
        self.aws_secrets = AWSSecretsManager()
        self._credentials_loaded = False
        # Initialize parent class attributes
        self.client_id = None
        self.client_secret = None
        self.refresh_token = None
        self._access_token = None
        self._token_expires_at = None
        
    async def _load_credentials(self):
        """Load credentials from AWS Secrets Manager in production"""
        if self._credentials_loaded:
            return
            
        if self.settings.use_aws_secrets:
            try:
                credentials = await self.aws_secrets.get_email_credentials("gmail")
                self.client_id = credentials["client_id"]
                self.client_secret = credentials["client_secret"]
                self.refresh_token = credentials["refresh_token"]
                self._credentials_loaded = True
                log.info("Gmail credentials loaded from AWS Secrets Manager")
            except Exception as e:
                log.error(f"Failed to load credentials from AWS: {str(e)}")
                raise
        else:
            # Fall back to environment variables for development
            self.client_id = self.settings.gmail_client_id
            self.client_secret = self.settings.gmail_client_secret
            self.refresh_token = self.settings.gmail_refresh_token
            self._credentials_loaded = True
            log.info("Gmail credentials loaded from environment variables")
    
    async def send(self, email: EmailRequest) -> EmailResponse:
        """Send email with credential loading"""
        await self._load_credentials()
        return await super().send(email)
    
    async def _refresh_access_token(self) -> str:
        """Refresh token and optionally update in AWS Secrets Manager"""
        await self._load_credentials()
        
        # Get new access token
        access_token = await super()._refresh_access_token()
        
        # In production, we might want to update the refresh token if it changes
        # (Gmail refresh tokens don't change, but other providers might)
        # This is a placeholder for providers that do rotate refresh tokens
        
        return access_token
    
    def is_configured(self) -> bool:
        """Check if Gmail API is properly configured"""
        if self.settings.use_aws_secrets:
            return self.aws_secrets.is_configured()
        else:
            return bool(
                self.settings.gmail_client_id and 
                self.settings.gmail_client_secret and 
                self.settings.gmail_refresh_token
            )