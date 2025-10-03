"""
Multi-tenant email service for handling user-specific Gmail OAuth and email sending
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from urllib.parse import urlencode
import base64
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from ..core.config import settings
from ..core.logging import log
from ..schemas.multi_tenant import (
    UserProfile,
    EmailAnalyticsResponse,
    EmailStatsDaily,
    TopRecipient,
    RecentEmail,
    MultiTenantEmailRequest,
    PlatformSummary
)
from ..schemas.responses import EmailResponse


class MultiTenantEmailService:
    """Service for managing multi-tenant email operations"""
    
    def __init__(self):
        self.gmail_client_id = settings.gmail_client_id
        self.gmail_client_secret = settings.gmail_client_secret
        # In production, this will use GCP Secret Manager or AWS Secrets Manager
        self.secrets_manager = None
        self._init_secrets_manager()
        
    def _init_secrets_manager(self):
        """Initialize appropriate secrets manager based on environment"""
        if settings.is_production:
            # In production, use cloud secrets manager
            if hasattr(settings, 'gcp_project_id') and settings.gcp_project_id:
                # Use GCP Secret Manager
                try:
                    from .gcp_secrets import GCPSecretsManager
                    self.secrets_manager = GCPSecretsManager()
                    log.info("Using GCP Secret Manager for multi-tenant")
                except ImportError:
                    log.warning("GCP Secret Manager not available")
            elif settings.aws_secrets_name:
                # Use AWS Secrets Manager
                try:
                    from .aws_secrets import AWSSecretsManager
                    self.secrets_manager = AWSSecretsManager()
                    log.info("Using AWS Secrets Manager for multi-tenant")
                except ImportError:
                    log.warning("AWS Secrets Manager not available")
    
    async def generate_oauth_url(self, user_id: str, redirect_uri: str) -> str:
        """
        Generate Gmail OAuth authorization URL for a user
        
        Args:
            user_id: Unique identifier for the user
            redirect_uri: OAuth redirect URI
            
        Returns:
            Authorization URL string
        """
        params = {
            'client_id': self.gmail_client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': user_id
        }
        
        base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        oauth_url = f"{base_url}?{urlencode(params)}"
        
        log.info(f"Generated OAuth URL for user: {user_id}")
        return oauth_url
    
    async def process_oauth_callback(
        self, 
        authorization_code: str, 
        user_id: str
    ) -> UserProfile:
        """
        Process OAuth callback and store user credentials
        
        Args:
            authorization_code: Authorization code from OAuth callback
            user_id: User identifier from state parameter
            
        Returns:
            UserProfile with connection details
        """
        # Exchange authorization code for tokens
        import requests
        
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': authorization_code,
            'client_id': self.gmail_client_id,
            'client_secret': self.gmail_client_secret,
            'redirect_uri': 'postmessage',  # For server-side flow
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        tokens = response.json()
        
        # Get user email address
        credentials = Credentials(
            token=tokens.get('access_token'),
            refresh_token=tokens.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self.gmail_client_id,
            client_secret=self.gmail_client_secret
        )
        
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile['emailAddress']
        
        # Store tokens in secrets manager
        if self.secrets_manager:
            secret_name = f"users/{user_id}/gmail"
            secret_data = {
                'refresh_token': tokens.get('refresh_token'),
                'access_token': tokens.get('access_token'),
                'email_address': email_address,
                'expires_at': (datetime.now() + timedelta(seconds=tokens.get('expires_in', 3600))).isoformat()
            }
            await self._store_user_secret(secret_name, secret_data)
        
        log.info(f"OAuth tokens stored for user {user_id}: {email_address}")
        
        return UserProfile(
            user_id=user_id,
            email_address=email_address,
            gmail_connected=True,
            connection_date=datetime.now(),
            total_emails_sent=0
        )
    
    async def _store_user_secret(self, secret_name: str, secret_data: Dict[str, Any]):
        """Store user secret in secrets manager"""
        if self.secrets_manager:
            if hasattr(self.secrets_manager, 'store_user_credentials'):
                # GCP Secret Manager
                user_id = secret_name.split('/')[1]  # Extract user_id from "users/{user_id}/gmail"
                await self.secrets_manager.store_user_credentials(user_id, secret_data)
            elif hasattr(self.secrets_manager, 'create_or_update_secret'):
                # AWS Secrets Manager
                secret_full_name = f"emailmcp/{secret_name}"
                import json
                result = self.secrets_manager.client.create_secret(
                    Name=secret_full_name,
                    SecretString=json.dumps(secret_data)
                ) if not self._secret_exists(secret_full_name) else \
                self.secrets_manager.client.update_secret(
                    SecretId=secret_full_name,
                    SecretString=json.dumps(secret_data)
                )
                log.info(f"Stored secret in AWS: {secret_full_name}")
        else:
            log.warning(f"No secrets manager configured - cannot store: {secret_name}")
    
    def _secret_exists(self, secret_name: str) -> bool:
        """Check if AWS secret exists"""
        try:
            self.secrets_manager.client.describe_secret(SecretId=secret_name)
            return True
        except:
            return False
    
    async def _get_user_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve user secret from secrets manager"""
        if self.secrets_manager:
            if hasattr(self.secrets_manager, 'get_user_credentials'):
                # GCP Secret Manager
                user_id = secret_name.split('/')[1]  # Extract user_id from "users/{user_id}/gmail"
                return await self.secrets_manager.get_user_credentials(user_id)
            elif hasattr(self.secrets_manager, 'get_secret'):
                # AWS Secrets Manager
                secret_full_name = f"emailmcp/{secret_name}"
                try:
                    result = await self.secrets_manager.get_email_credentials(secret_name)
                    return result
                except:
                    return None
        else:
            log.warning(f"No secrets manager configured - cannot retrieve: {secret_name}")
        return None
    
    async def get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Get Gmail credentials for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Google Credentials object or None
        """
        secret_name = f"users/{user_id}/gmail"
        secret_data = await self._get_user_secret(secret_name)
        
        if not secret_data:
            log.warning(f"No credentials found for user: {user_id}")
            return None
        
        credentials = Credentials(
            token=secret_data.get('access_token'),
            refresh_token=secret_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self.gmail_client_id,
            client_secret=self.gmail_client_secret
        )
        
        # Refresh token if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Update stored access token
            secret_data['access_token'] = credentials.token
            secret_data['expires_at'] = credentials.expiry.isoformat() if credentials.expiry else None
            await self._store_user_secret(secret_name, secret_data)
        
        return credentials
    
    async def send_user_email(
        self, 
        user_id: str, 
        email: MultiTenantEmailRequest
    ) -> EmailResponse:
        """
        Send email using user's Gmail credentials
        
        Args:
            user_id: User identifier
            email: Email request details
            
        Returns:
            EmailResponse with status and message ID
        """
        # Get user credentials
        credentials = await self.get_user_credentials(user_id)
        if not credentials:
            raise ValueError(f"User {user_id} has not connected Gmail account")
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Create message
        message = self._create_message(email)
        
        try:
            # Send message
            result = service.users().messages().send(
                userId='me',
                body={'raw': message}
            ).execute()
            
            log.info(f"Email sent for user {user_id}: {result['id']}")
            
            return EmailResponse(
                status="success",
                message_id=result['id'],
                provider="gmail_api",
                timestamp=datetime.now()
            )
        except Exception as e:
            log.error(f"Failed to send email for user {user_id}: {e}")
            return EmailResponse(
                status="failed",
                provider="gmail_api",
                timestamp=datetime.now(),
                error=str(e)
            )
    
    def _create_message(self, email: MultiTenantEmailRequest) -> str:
        """Create a message for sending via Gmail API"""
        message = MIMEText(email.body, email.body_type)
        message['to'] = ', '.join(email.to)
        message['subject'] = email.subject
        
        if email.cc:
            message['cc'] = ', '.join(email.cc)
        if email.bcc:
            message['bcc'] = ', '.join(email.bcc)
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return raw
    
    async def get_user_profile(self, user_id: str) -> UserProfile:
        """
        Get user profile and Gmail connection status
        
        Args:
            user_id: User identifier
            
        Returns:
            UserProfile with connection details
        """
        secret_name = f"users/{user_id}/gmail"
        secret_data = await self._get_user_secret(secret_name)
        
        if not secret_data:
            return UserProfile(
                user_id=user_id,
                gmail_connected=False
            )
        
        return UserProfile(
            user_id=user_id,
            email_address=secret_data.get('email_address'),
            gmail_connected=True,
            connection_date=datetime.fromisoformat(secret_data.get('connection_date', datetime.now().isoformat())),
            total_emails_sent=0  # TODO: Get from database
        )
    
    async def log_email_transaction(
        self, 
        user_id: str, 
        email: MultiTenantEmailRequest, 
        result: EmailResponse
    ):
        """
        Log email transaction for analytics
        
        Args:
            user_id: User identifier
            email: Email request details
            result: Email send result
        """
        # TODO: Implement database logging
        log.info(f"Logged email for user {user_id}: status={result.status}")
    
    async def get_user_analytics(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 100
    ) -> EmailAnalyticsResponse:
        """
        Get email analytics for a user
        
        Args:
            user_id: User identifier
            start_date: Start date for analytics
            end_date: End date for analytics
            limit: Maximum number of recent emails to return
            
        Returns:
            EmailAnalyticsResponse with statistics
        """
        # TODO: Implement database queries
        # This is a placeholder implementation
        return EmailAnalyticsResponse(
            user_id=user_id,
            date_range={"start": start_date, "end": end_date},
            total_emails=0,
            successful_emails=0,
            failed_emails=0,
            success_rate=0.0,
            emails_by_day=[],
            top_recipients=[],
            recent_emails=[]
        )
    
    async def get_platform_summary(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> PlatformSummary:
        """
        Get platform-wide email analytics
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            
        Returns:
            PlatformSummary with platform statistics
        """
        # TODO: Implement database queries
        # This is a placeholder implementation
        return PlatformSummary(
            total_users=0,
            active_users=0,
            total_emails_sent=0,
            emails_today=0,
            emails_this_week=0,
            overall_success_rate=0.0,
            top_senders=[],
            usage_trends=[]
        )
    
    async def disconnect_user_gmail(self, user_id: str):
        """
        Disconnect user's Gmail account
        
        Args:
            user_id: User identifier
        """
        secret_name = f"users/{user_id}/gmail"
        # TODO: Implement secret deletion
        log.info(f"Disconnected Gmail for user: {user_id}")
