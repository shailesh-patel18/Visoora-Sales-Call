import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class PlatformContext(BaseModel):
    """
    The Global Context object injected into every request, event, and background task.
    Replaces massive parameter lists (tenant, user, brain, trace_id) across the system.
    """
    # Identifiers
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: Optional[str] = None
    
    # Mission / Workflow Scope
    mission_id: Optional[str] = None
    workflow_id: Optional[str] = None
    task_id: Optional[str] = None
    
    # Knowledge Scope
    business_brain_id: Optional[str] = None
    
    # Feature Flags & Permissions
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    roles: list[str] = Field(default_factory=list)
    
    # Execution Metadata
    correlation_id: Optional[str] = None
    
    def extend(self, **kwargs) -> 'PlatformContext':
        """Creates a new context extending the current one (useful when branching into a sub-task)."""
        current_data = self.dict()
        current_data.update(kwargs)
        return PlatformContext(**current_data)
