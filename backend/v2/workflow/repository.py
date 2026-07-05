from abc import ABC, abstractmethod
from typing import Optional
import structlog
from v2.workflow.models import WorkflowExecutionState
from v2.foundation.context.middleware import get_platform_context

logger = structlog.get_logger("workflow_repository")

class IWorkflowRepository(ABC):
    """
    Port (Interface) for persisting active workflow execution states.
    """
    @abstractmethod
    async def save(self, state: WorkflowExecutionState) -> WorkflowExecutionState:
        pass
        
    @abstractmethod
    async def get(self, execution_id: str) -> Optional[WorkflowExecutionState]:
        pass

class MemoryWorkflowAdapter(IWorkflowRepository):
    """
    In-memory storage for local dev.
    """
    def __init__(self):
        self._states = {}
        
    async def save(self, state: WorkflowExecutionState) -> WorkflowExecutionState:
        ctx = get_platform_context()
        trace_id = ctx.trace_id if ctx else "unknown"
        
        self._states[state.execution_id] = state
        logger.info("workflow_saved", execution_id=state.execution_id, status=state.status.value, trace_id=trace_id)
        return state
        
    async def get(self, execution_id: str) -> Optional[WorkflowExecutionState]:
        return self._states.get(execution_id)

# Global Instance for DI
workflow_repository = MemoryWorkflowAdapter()
