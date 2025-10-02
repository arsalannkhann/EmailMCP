from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal

class EmailRequest(BaseModel):
    """Request model for sending emails"""
    provider: Literal["gmail_api", "gmail", "outlook", "smtp", "auto"] = Field(
        default="auto",
        description="Email provider to use (auto = best available)"
    )
    to: List[EmailStr] = Field(
        min_length=1,
        description="List of recipient email addresses"
    )
    subject: str = Field(
        min_length=1,
        max_length=998,
        description="Email subject line"
    )
    body: str = Field(
        description="Email body content"
    )
    from_email: EmailStr = Field(
        description="Sender email address"
    )
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    html: bool = Field(
        default=False,
        description="Whether body is HTML formatted"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "gmail",
                "to": ["recipient@example.com"],
                "subject": "Test Email",
                "body": "This is a test email",
                "from_email": "sender@example.com",
                "html": False
            }
        }
