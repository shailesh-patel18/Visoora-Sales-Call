from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class WorkflowStepDefinition(BaseModel):
    id: str
    action: str  # e.g. 'analyze_website'
    agent: str   # e.g. 'ResearchAgent'
    inputs: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    retries: int = 0
    requires_approval: bool = False

class WorkflowDefinition(BaseModel):
    id: str
    version: str
    goal: str
    steps: List[WorkflowStepDefinition]

class WorkflowContext(BaseModel):
    """
    Shared memory graph that persists across workflow steps.
    """
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    step_outputs: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)

class WorkflowExecutionState(BaseModel):
    """
    State of an active or completed workflow.
    """
    execution_id: str
    tenant_id: str
    user_id: Optional[str] = None
    workflow_id: str
    workflow_version: str
    goal: str
    
    status: str = "pending" # pending, running, paused, completed, failed
    current_step: Optional[str] = None
    completed_steps: List[str] = Field(default_factory=list)
    
    context: WorkflowContext = Field(default_factory=WorkflowContext)
    
    execution_mode: str = "sync" # sync, async
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def mark_started(self):
        self.status = "running"
        self.started_at = datetime.utcnow().isoformat()
        
    def mark_completed(self):
        self.status = "completed"
        self.completed_at = datetime.utcnow().isoformat()
        
    def mark_failed(self, error: str):
        self.status = "failed"
        self.context.errors.append(error)
        self.completed_at = datetime.utcnow().isoformat()
