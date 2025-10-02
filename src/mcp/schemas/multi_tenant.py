from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# OAuth Request/Response Models
class OAuthRequest(BaseModel):
    user_id: str
    redirect_uri: str

class OAuthResponse(BaseModel):
    authorization_url: str
    state: str

# Multi-tenant Email Models
class MultiTenantEmailRequest(BaseModel):
    to: List[EmailStr]
    subject: str
    body: str
    body_type: str = "text"  # "text" or "html"
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    attachments: Optional[List[Dict[str, Any]]] = None

# User Profile Models
class UserProfile(BaseModel):
    user_id: str
    email_address: Optional[str] = None
    gmail_connected: bool = False
    connection_date: Optional[datetime] = None
    last_used: Optional[datetime] = None
    total_emails_sent: int = 0

# Analytics Models
class EmailStatsDaily(BaseModel):
    date: str
    total: int
    successful: int
    failed: int

class TopRecipient(BaseModel):
    email: str
    count: int

class RecentEmail(BaseModel):
    id: str
    to_emails: List[str]
    subject: str
    status: str
    sent_at: datetime
    message_id: Optional[str] = None

class EmailAnalyticsResponse(BaseModel):
    user_id: str
    date_range: Dict[str, datetime]
    total_emails: int
    successful_emails: int
    failed_emails: int
    success_rate: float
    emails_by_day: List[EmailStatsDaily]
    top_recipients: List[TopRecipient]
    recent_emails: List[RecentEmail]

# Platform Summary Models
class PlatformSummary(BaseModel):
    total_users: int
    active_users: int
    total_emails_sent: int
    emails_today: int
    emails_this_week: int
    overall_success_rate: float
    top_senders: List[Dict[str, Any]]
    usage_trends: List[EmailStatsDaily]