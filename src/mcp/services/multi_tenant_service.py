"""
Multi-tenant email service for handling user-specific Gmail OAuth and email sending
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
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
from .firestore_service import FirestoreService

# OAuth Scopes - aligned with Flask MCP for consistency
GMAIL_OAUTH_SCOPES = [
    'openid',
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

class MultiTenantEmailService:
    """Service for managing multi-tenant email operations"""
    
    def __init__(self):
        self.gmail_client_id = settings.gmail_client_id
        self.gmail_client_secret = settings.gmail_client_secret
        # In production, this will use GCP Secret Manager or AWS Secrets Manager
        self.secrets_manager = None
        self.firestore_service = FirestoreService()
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
            'scope': ' '.join(GMAIL_OAUTH_SCOPES),
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
        user_id: str,
        redirect_uri: Optional[str] = None
    ) -> UserProfile:
        """
        Process OAuth callback and store user credentials
        
        Args:
            authorization_code: Authorization code from OAuth callback
            user_id: User identifier from state parameter
            redirect_uri: Redirect URI used in authorization (must match)
            
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
            'redirect_uri': redirect_uri or 'postmessage',  # Use provided redirect_uri or default
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
        
        # Create/update user profile in Firestore
        user_profile_data = {
            'id': user_id,
            'email': email_address,
            'gmail_connected': True,
            'gmail_connected_at': datetime.now(timezone.utc).isoformat(),
            'gmail_email': email_address,
            'gmail_refresh_token_stored': True,
            'total_emails_sent': 0,
            'account_status': 'active',
            'subscription_tier': 'free',
            'rate_limit_quota': 100,
            'rate_limit_used': 0,
            'last_login': datetime.now(timezone.utc).isoformat()
        }
        
        await self.firestore_service.create_user_profile(user_profile_data)
        
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
            
            response = EmailResponse(
                status="sent",
                message_id=result['id'],
                provider="gmail_api",
                timestamp=datetime.now()
            )
            
            # Log the transaction to Firestore
            await self.log_email_transaction(user_id, email, response)
            
            return response
            
        except Exception as e:
            log.error(f"Failed to send email for user {user_id}: {e}")
            
            response = EmailResponse(
                status="failed",
                provider="gmail_api",
                timestamp=datetime.now(),
                error=str(e)
            )
            
            # Log the failed transaction to Firestore
            await self.log_email_transaction(user_id, email, response)
            
            return response
    
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
            UserProfile with current status
        """
        # Get user profile from Firestore
        profile_data = await self.firestore_service.get_user_profile(user_id)
        
        if profile_data:
            # Parse connection date
            connection_date = None
            if profile_data.get('gmail_connected_at'):
                try:
                    connection_date = datetime.fromisoformat(profile_data['gmail_connected_at'].replace('Z', '+00:00'))
                except:
                    connection_date = None
            
            return UserProfile(
                user_id=user_id,
                email_address=profile_data.get('email', ''),
                gmail_connected=profile_data.get('gmail_connected', False),
                connection_date=connection_date,
                total_emails_sent=profile_data.get('total_emails_sent', 0)
            )
        else:
            # Return default profile if not found
            return UserProfile(
                user_id=user_id,
                email_address="",
                gmail_connected=False,
                connection_date=None,
                total_emails_sent=0
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
        # Log to Firestore
        email_data = {
            'from_email': email.from_email,
            'to_emails': email.to_emails,
            'cc_emails': email.cc_emails or [],
            'bcc_emails': email.bcc_emails or [],
            'subject': email.subject,
            'body': email.body,
            'html_body': email.html_body,
            'attachments': email.attachments or []
        }
        
        result_data = {
            'status': result.status,
            'message_id': result.message_id,
            'error': result.error
        }
        
        await self.firestore_service.log_email_transaction(user_id, email_data, result_data)
        
        # Update user statistics
        if result.status == 'sent':
            await self.firestore_service.update_user_stats(user_id, 1)
        
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
        # Get analytics from Firestore
        analytics_data = await self.firestore_service.get_user_analytics(user_id, start_date, end_date)
        
        # Get recent email logs
        recent_logs = await self.firestore_service.get_user_email_logs(user_id, limit, start_date, end_date)
        
        # Convert logs to RecentEmail objects
        recent_emails = []
        for log_entry in recent_logs:
            recent_emails.append(RecentEmail(
                subject=log_entry.get('subject', ''),
                to_emails=log_entry.get('to_emails', []),
                sent_at=log_entry.get('sent_at', ''),
                status=log_entry.get('status', 'unknown')
            ))
        
        # Convert daily stats
        emails_by_day = []
        for day_data in analytics_data.get('emails_by_day', []):
            emails_by_day.append(EmailStatsDaily(
                date=day_data.get('date', ''),
                count=day_data.get('count', 0)
            ))
        
        # Convert top recipients
        top_recipients = []
        for recipient_data in analytics_data.get('top_recipients', []):
            top_recipients.append(TopRecipient(
                email=recipient_data.get('email', ''),
                count=recipient_data.get('count', 0)
            ))
        
        return EmailAnalyticsResponse(
            user_id=user_id,
            date_range={"start": start_date, "end": end_date},
            total_emails=analytics_data.get('total_emails', 0),
            successful_emails=analytics_data.get('successful_emails', 0),
            failed_emails=analytics_data.get('failed_emails', 0),
            success_rate=analytics_data.get('success_rate', 0.0),
            emails_by_day=emails_by_day,
            top_recipients=top_recipients,
            recent_emails=recent_emails
        )
    
    async def get_platform_summary(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> PlatformSummary:
        """
        Get platform-wide summary statistics
        
        Args:
            start_date: Start date for summary
            end_date: End date for summary
            
        Returns:
            PlatformSummary with aggregate statistics
        """
        # Get platform metrics from Firestore
        # For now, get metrics for the end date
        metrics_data = await self.firestore_service.get_platform_metrics(end_date)
        
        # Get today's metrics
        today = datetime.now(timezone.utc)
        today_metrics = await self.firestore_service.get_platform_metrics(today)
        
        # Calculate week metrics (simplified - just use today's data)
        emails_today = today_metrics.get('emails_sent', 0)
        emails_this_week = emails_today * 7  # Simplified calculation
        
        # Create usage trends (simplified)
        usage_trends = []
        current_date = start_date
        while current_date <= end_date:
            day_metrics = await self.firestore_service.get_platform_metrics(current_date)
            usage_trends.append(EmailStatsDaily(
                date=current_date.strftime('%Y-%m-%d'),
                total=day_metrics.get('emails_sent', 0),
                successful=day_metrics.get('emails_sent', 0) - day_metrics.get('emails_failed', 0),
                failed=day_metrics.get('emails_failed', 0)
            ))
            current_date += timedelta(days=1)
            if len(usage_trends) >= 7:  # Limit to 7 days to avoid long queries
                break
        
        return PlatformSummary(
            total_users=metrics_data.get('total_users', 0),
            active_users=metrics_data.get('active_users', 0),
            total_emails_sent=metrics_data.get('emails_sent', 0),
            emails_today=emails_today,
            emails_this_week=emails_this_week,
            overall_success_rate=metrics_data.get('success_rate', 0.0),
            top_senders=[],  # TODO: Implement top senders query
            usage_trends=usage_trends
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
