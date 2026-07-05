from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class BuyerPersona(BaseModel):
    title: str
    pain_points: List[str]
    goals: List[str]

class ProductOrService(BaseModel):
    name: str
    description: str
    key_features: List[str]

class Competitor(BaseModel):
    name: str
    differentiator: str

class BusinessBrain(BaseModel):
    """
    The central knowledge core of the Visoora AI OS. 
    Every agent task enriches this object over time.
    """
    company_name: str = ""
    domain: str = ""
    business_summary: str = ""
    products_and_services: List[ProductOrService] = Field(default_factory=list)
    ideal_customer_profiles: List[str] = Field(default_factory=list)
    buyer_personas: List[BuyerPersona] = Field(default_factory=list)
    competitors: List[Competitor] = Field(default_factory=list)
    market_opportunities: List[str] = Field(default_factory=list)
    recommended_strategies: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    buying_signals: List[str] = Field(default_factory=list)
    pricing_model: Optional[str] = None
