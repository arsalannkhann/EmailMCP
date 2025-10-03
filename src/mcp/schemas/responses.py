from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime

class EmailResponse(BaseModel):
    """Response model for email operations"""
    status: Literal["success", "pending", "failed"]
    message_id: Optional[str] = None
    provider: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None

class ErrorDetail(BaseModel):
    """Standardized error response"""
    code: str
    message: str
    detail: Optional[str] = None

# Multi-tenant response models
class OAuthResponse(BaseModel):
    """OAuth authorization response"""
    authorization_url: str
    state: str

class EmailStatsDaily(BaseModel):
    """Daily email statistics"""
    date: str
    total: int
    successful: int
    failed: int

class TopRecipient(BaseModel):
    """Top email recipient"""
    email: str
    count: int

class RecentEmail(BaseModel):
    """Recent email record"""
    id: str
    to_emails: List[str]
    subject: str
    status: str
    sent_at: datetime
    message_id: Optional[str] = None

class EmailAnalyticsResponse(BaseModel):
    """Email analytics for a user"""
    user_id: str
    date_range: Dict[str, datetime]
    total_emails: int
    successful_emails: int
    failed_emails: int
    success_rate: float
    emails_by_day: List[EmailStatsDaily]
    top_recipients: List[TopRecipient]
    recent_emails: List[RecentEmail]
