import uuid
import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    MEETING_BOOKED = "meeting_booked"
    DISQUALIFIED = "disqualified"

class Lead(BaseModel):
    """
    Domain entity representing a potential customer.
    Completely decoupled from the AI ProspectingAgent.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    company_name: str
    company_domain: Optional[str] = None
    
    status: LeadStatus = LeadStatus.NEW
    score: Optional[int] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict) # E.g., intent signals, source
    
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class PipelineStage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    order: int

class CRMContext(BaseModel):
    """
    Global CRM configuration for a tenant.
    """
    tenant_id: str
    stages: List[PipelineStage] = Field(default_factory=list)

class DraftStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"
    SEND_FAILED = "send_failed"

class EmailDraft(BaseModel):
    """
    A drafted email associated with a Lead. Requires approval before sending.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    lead_id: str
    
    subject: str
    body: str
    
    evidence_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    status: DraftStatus = DraftStatus.PENDING_APPROVAL
    
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
