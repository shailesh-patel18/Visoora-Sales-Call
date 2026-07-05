import uuid
import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class MissionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class Mission(BaseModel):
    """
    A top-level autonomous objective (e.g., "Find 100 prospects and book 5 meetings").
    A Mission consists of multiple Workflows.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    goal_description: str
    
    status: MissionStatus = MissionStatus.DRAFT
    active_workflows: List[str] = Field(default_factory=list) # List of Workflow Execution IDs
    completed_workflows: List[str] = Field(default_factory=list)
    
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
