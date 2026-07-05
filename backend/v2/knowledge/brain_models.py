import uuid
import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class CompanyProfile(BaseModel):
    name: str
    description: str
    website: Optional[str] = None
    industry: Optional[str] = None
    value_props: List[str] = Field(default_factory=list)

class BuyerPersona(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    pain_points: List[str] = Field(default_factory=list)
    motivations: List[str] = Field(default_factory=list)

class IdealCustomerProfile(BaseModel):
    target_industries: List[str] = Field(default_factory=list)
    company_size_range: Optional[str] = None
    geographies: List[str] = Field(default_factory=list)
    key_technologies: List[str] = Field(default_factory=list)

class Competitor(BaseModel):
    name: str
    weaknesses: List[str] = Field(default_factory=list)
    our_differentiators: List[str] = Field(default_factory=list)

class ObjectionRebuttal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    objection_theme: str
    rebuttal_script: str
    success_rate: Optional[float] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class BusinessBrain(BaseModel):
    """
    The structured, centralized knowledge base for a tenant.
    Replaces the monolithic JSON blob from v1.
    """
    id: str
    tenant_id: str
    version: int = 1
    
    company: CompanyProfile
    icp: IdealCustomerProfile = Field(default_factory=IdealCustomerProfile)
    personas: List[BuyerPersona] = Field(default_factory=list)
    competitors: List[Competitor] = Field(default_factory=list)
    objections: List[ObjectionRebuttal] = Field(default_factory=list)
    faqs: List[Dict[str, str]] = Field(default_factory=list)
    
    updated_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
