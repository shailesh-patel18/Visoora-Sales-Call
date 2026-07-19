from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid

class MissionRequest(BaseModel):
    """
    Standard request payload to start or resume a mission on the platform.
    """
    mission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = None
    resume: bool = False
