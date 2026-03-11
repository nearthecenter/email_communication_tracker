"""Data models for email tracking."""

from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class EmailStatus(str, Enum):
    """Email status enum."""
    INCOMING = "incoming"
    PENDING = "pending"
    ONGOING = "ongoing"  # Email opened/read
    ANSWERED = "answered"
    MANUAL_REPLY = "manual_reply"
    DONE = "done"  # Reply sent (auto or manual)


class Email(BaseModel):
    """Email data model."""
    email_id: str = Field(..., description="Gmail message ID")
    thread_id: Optional[str] = Field(None, description="Gmail thread ID")
    message_header_id: Optional[str] = Field(None, description="RFC 2822 Message-ID header")
    from_email: str = Field(..., description="Sender email address")
    from_name: Optional[str] = Field(None, description="Sender name")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body text")
    received_at: datetime = Field(default_factory=datetime.utcnow)
    category: Optional[str] = Field(None, description="Auto-detected category")
    status: EmailStatus = Field(default=EmailStatus.INCOMING)
    matched_response: Optional[str] = Field(None, description="Matched response from docx if applicable")
    reply_sent: bool = Field(default=False)
    reply_body: Optional[str] = Field(None, description="Content of sent reply")
    reply_sent_at: Optional[datetime] = Field(None)
    notes: Optional[str] = Field(None, description="Additional notes")


class EmailLog(BaseModel):
    """Email log entry for Google Sheets."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    email_id: str
    from_email: str
    subject: str
    category: str
    status: str
    matched_response: Optional[str] = None
    reply_sent: bool
    reply_sent_at: Optional[datetime] = None
    notes: Optional[str] = None

    @classmethod
    def create_from_email(cls, email: Email) -> "EmailLog":
        """Create log entry from Email model."""
        return cls(
            email_id=getattr(email, 'email_id', 'unknown'),
            from_email=getattr(email, 'from_email', 'unknown@example.com'),
            subject=getattr(email, 'subject', '(No Subject)'),
            category=getattr(email, 'category', 'uncategorized') or "uncategorized",
            status=getattr(email, 'status', EmailStatus.INCOMING).value if hasattr(email, 'status') else 'incoming',
            matched_response=getattr(email, 'matched_response', None),
            reply_sent=getattr(email, 'reply_sent', False),
            reply_sent_at=getattr(email, 'reply_sent_at', None),
            notes=getattr(email, 'notes', None),
        )
