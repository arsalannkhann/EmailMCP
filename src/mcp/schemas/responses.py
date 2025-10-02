from pydantic import BaseModel, Field
from typing import Optional, Literal
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
