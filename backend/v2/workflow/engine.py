from typing import List, Dict, Any, Optional
import structlog
from v2.workflow.models import WorkflowExecutionState, WorkflowDefinition, WorkflowStep, StepStatus
from v2.workflow.repository import workflow_repository
from v2.foundation.events.memory_adapter import event_bus
from v2.foundation.events.bus import BaseDomainEvent

logger = structlog.get_logger("workflow_engine")

class WorkflowEvent(BaseDomainEvent):
    event_name: str = "WorkflowEvent"

class WorkflowEngine:
    """
    Temporal.io inspired DAG execution engine.
    Given a WorkflowExecutionState, it determines which steps are ready to run,
    dispatches them, and handles state transitions.
    """
    
    @staticmethod
    async def initialize(tenant_id: str, definition: WorkflowDefinition, payload: Dict[str, Any] = None) -> WorkflowExecutionState:
        """Creates a new execution state from a definition."""
        state = WorkflowExecutionState(
            tenant_id=tenant_id,
            workflow_name=definition.workflow_name,
            steps={step.step_id: step.copy() for step in definition.steps}
        )
        
        # Inject initial payload into steps with no dependencies
        if payload:
            for step in state.steps.values():
                if not step.depends_on:
                    step.payload.update(payload)
                    
        await workflow_repository.save(state)
        
        logger.info("workflow_initialized", execution_id=state.execution_id)
        
        # Publish event
        evt = WorkflowEvent(
            tenant_id=tenant_id,
            trace_id="system", # Would grab from context
            payload={"action": "started", "execution_id": state.execution_id}
        )
        await event_bus.publish(evt)
        
        return state

    @staticmethod
    async def get_executable_steps(execution_id: str) -> List[WorkflowStep]:
        """Returns all steps that have their dependencies met and are PENDING."""
        state = await workflow_repository.get(execution_id)
        if not state or state.has_failed() or state.is_complete():
            return []
            
        executable = []
        for step in state.steps.values():
            if step.status == StepStatus.PENDING:
                # Check if all dependencies are COMPLETED or SKIPPED
                deps_met = True
                for dep_id in step.depends_on:
                    dep_step = state.steps.get(dep_id)
                    if not dep_step or dep_step.status not in (StepStatus.COMPLETED, StepStatus.SKIPPED):
                        deps_met = False
                        break
                
                if deps_met:
                    executable.append(step)
                    
        return executable

    @staticmethod
    async def update_step_status(execution_id: str, step_id: str, status: StepStatus, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Updates the status of a specific step and triggers a save."""
        state = await workflow_repository.get(execution_id)
        if not state:
            return
            
        step = state.steps.get(step_id)
        if not step:
            return
            
        step.status = status
        if result:
            step.result = result
        if error:
            step.error = error
            
        await workflow_repository.save(state)
        
        # Automatically determine overall workflow status
        if state.has_failed():
            state.status = StepStatus.FAILED
            logger.error("workflow_failed", execution_id=execution_id, failed_step=step_id)
        elif state.is_complete():
            state.status = StepStatus.COMPLETED
            logger.info("workflow_completed", execution_id=execution_id)
            
        await workflow_repository.save(state)
