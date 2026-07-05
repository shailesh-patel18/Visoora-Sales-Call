import uuid
import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class CallOutcome(str, Enum):
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    NOT_INTERESTED = "not_interested"
    MEETING_BOOKED = "meeting_booked"
    CALL_BACK_LATER = "call_back_later"
    FAILED = "failed"

class SalesCall(BaseModel):
    """
    Domain entity representing a phone call execution and outcome.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    lead_id: str
    
    status: str = "initiated"
    outcome: Optional[CallOutcome] = None
    
    duration_seconds: int = 0
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
