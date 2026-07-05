import structlog
from typing import Dict, Any
from v2.mission.models import Mission, MissionStatus
from v2.mission.repository import mission_repository
from v2.workflow.engine import WorkflowEngine
from v2.workflow.models import StepStatus
from v2.agents.base_agent import BaseAgent
from v2.foundation.events.memory_adapter import event_bus
from v2.foundation.events.bus import BaseDomainEvent

logger = structlog.get_logger("mission_orchestrator")

class ApprovalRequestedEvent(BaseDomainEvent):
    event_name: str = "ApprovalRequested"

class MissionOrchestrator:
    """
    Bridges the Workflow Engine (DAG) and the Agent Platform.
    It dispatches tasks to agents and handles human-in-the-loop approval gates.
    """
    
    @staticmethod
    async def dispatch_executable_steps(mission_id: str):
        """
        Finds all active workflows for a mission, gets their executable steps, 
        and spins up the correct agents to perform the work.
        """
        mission = await mission_repository.get(mission_id)
        if not mission or mission.status != MissionStatus.ACTIVE:
            return
            
        for execution_id in mission.active_workflows:
            steps_to_run = await WorkflowEngine.get_executable_steps(execution_id)
            
            for step in steps_to_run:
                # Mark step as running
                await WorkflowEngine.update_step_status(execution_id, step.step_id, StepStatus.RUNNING)
                
                # Check if this step is an approval gate
                if step.action == "request_approval":
                    await MissionOrchestrator._request_human_approval(mission, execution_id, step.step_id, step.payload)
                    continue
                    
                # Dispatch to agent
                if step.action == "execute_agent":
                    # In a real system, this would push to an async Queue (Redis/Celery)
                    # For now, we simulate async dispatch
                    await MissionOrchestrator._simulate_agent_execution(mission, execution_id, step.step_id, step.agent_type, step.payload)

    @staticmethod
    async def _request_human_approval(mission: Mission, execution_id: str, step_id: str, payload: Dict[str, Any]):
        """Pauses the step and emits an event for the Command Center UI."""
        logger.info("human_approval_requested", mission_id=mission.id, step_id=step_id)
        
        await WorkflowEngine.update_step_status(execution_id, step_id, StepStatus.WAITING_APPROVAL)
        
        evt = ApprovalRequestedEvent(
            tenant_id=mission.tenant_id,
            trace_id="system",
            payload={
                "mission_id": mission.id,
                "workflow_id": execution_id,
                "step_id": step_id,
                "approval_context": payload
            }
        )
        await event_bus.publish(evt)
        
    @staticmethod
    async def _simulate_agent_execution(mission: Mission, execution_id: str, step_id: str, agent_type: str, payload: Dict[str, Any]):
        """Stub for actual agent factory and execution loop."""
        logger.info("agent_dispatched", agent_type=agent_type, step_id=step_id)
        
        # Simulate work being done
        await __import__("asyncio").sleep(0.5)
        
        # Mark Complete
        await WorkflowEngine.update_step_status(
            execution_id=execution_id, 
            step_id=step_id, 
            status=StepStatus.COMPLETED,
            result={"output": f"Simulated output from {agent_type}"}
        )
        
        # Trigger next steps in the DAG
        await MissionOrchestrator.dispatch_executable_steps(mission.id)
