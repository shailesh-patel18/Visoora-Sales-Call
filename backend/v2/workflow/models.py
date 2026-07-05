import uuid
import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"
    SKIPPED = "skipped"

class WorkflowStep(BaseModel):
    step_id: str
    action: str  # e.g., "execute_agent", "wait", "request_approval"
    depends_on: List[str] = Field(default_factory=list)
    agent_type: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # State tracking
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    retries: int = 0
    max_retries: int = 3
    error: Optional[str] = None

class WorkflowDefinition(BaseModel):
    """
    A declarative definition of a workflow, independent of execution state.
    """
    workflow_name: str
    version: int = 1
    steps: List[WorkflowStep] = Field(default_factory=list)

class WorkflowExecutionState(BaseModel):
    """
    The active state of a running workflow.
    """
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    mission_id: Optional[str] = None
    workflow_name: str
    
    status: StepStatus = StepStatus.PENDING
    steps: Dict[str, WorkflowStep] = Field(default_factory=dict) # Map of step_id -> Step state
    
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    
    def is_complete(self) -> bool:
        return all(s.status == StepStatus.COMPLETED or s.status == StepStatus.SKIPPED for s in self.steps.values())
        
    def has_failed(self) -> bool:
        return any(s.status == StepStatus.FAILED for s in self.steps.values())
