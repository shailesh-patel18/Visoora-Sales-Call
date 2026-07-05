import yaml
import asyncio
import uuid
import structlog
from typing import Dict, Any, List
from datetime import datetime

from .models import WorkflowDefinition, WorkflowExecutionState, WorkflowStepDefinition
from .events import WorkflowEventPublisher
from server.worker import enqueue_background_job
from ai_platform.agents.research_agent import ResearchAgent
from ai_platform.agents.email_agent import EmailAgent
from ai_platform.agents.prospecting_agent import ProspectingAgent

logger = structlog.get_logger("visoora_workflow_engine")

# Registry of available agents for the engine to instantiate
AGENT_REGISTRY = {
    "ResearchAgent": ResearchAgent,
    "EmailAgent": EmailAgent,
    "ProspectingAgent": ProspectingAgent,
}

class WorkflowEngine:
    def __init__(self, tenant_id: str, user_id: str = None):
        self.tenant_id = tenant_id
        self.user_id = user_id

    def load_definition(self, yaml_path: str) -> WorkflowDefinition:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        workflow_data = data.get("workflow", {})
        steps_data = data.get("steps", [])
        
        steps = []
        for s in steps_data:
            steps.append(WorkflowStepDefinition(
                id=s["id"],
                action=s["action"],
                agent=s["agent"],
                inputs=s.get("inputs", {}),
                depends_on=s.get("depends_on", []),
                retries=s.get("retries", 0),
                requires_approval=s.get("requires_approval", False)
            ))
            
        return WorkflowDefinition(
            id=workflow_data.get("id"),
            version=str(workflow_data.get("version")),
            goal=data.get("goal", ""),
            steps=steps
        )

    async def execute(self, yaml_path: str, initial_context: Dict[str, Any] = None, mode: str = "sync") -> WorkflowExecutionState:
        """
        Main entry point to execute a workflow.
        If mode="async", enqueues a background job and returns pending state immediately.
        If mode="sync", executes in-memory and returns completed state.
        """
        definition = self.load_definition(yaml_path)
        execution_id = str(uuid.uuid4())
        
        state = WorkflowExecutionState(
            execution_id=execution_id,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            workflow_id=definition.id,
            workflow_version=definition.version,
            goal=definition.goal,
            execution_mode=mode
        )
        
        if initial_context:
            state.context.artifacts.update(initial_context)
            
        WorkflowEventPublisher.emit("WorkflowStarted", execution_id, self.tenant_id, {"goal": state.goal, "mode": mode})

        if mode == "async":
            await enqueue_background_job(
                tenant_id=self.tenant_id,
                job_type="workflow_execution",
                payload={
                    "execution_id": execution_id,
                    "yaml_path": yaml_path,
                    "state": state.model_dump()
                }
            )
            return state

        # Synchronous Execution
        state.mark_started()
        await self._run_dag(state, definition)
        return state

    async def _run_dag(self, state: WorkflowExecutionState, definition: WorkflowDefinition):
        """
        Runs the DAG. For simplicity, we process nodes that have their dependencies met.
        In a full implementation, we'd use asyncio.gather for parallel nodes.
        """
        remaining_steps = {s.id: s for s in definition.steps}
        
        while remaining_steps and state.status == "running":
            # Find all ready steps
            ready_steps = []
            for step_id, step_def in remaining_steps.items():
                # Check if all dependencies are in completed_steps
                if all(dep in state.completed_steps for dep in step_def.depends_on):
                    ready_steps.append(step_def)
            
            if not ready_steps:
                # Cycle detected or blocked on dependencies
                state.mark_failed("Deadlock or missing dependencies in DAG.")
                WorkflowEventPublisher.emit("WorkflowFailed", state.execution_id, self.tenant_id, {"error": "Deadlock"})
                break

            # Execute parallel steps using gather
            results = await asyncio.gather(*[self._execute_step(state, step) for step in ready_steps], return_exceptions=True)
            
            for step, result in zip(ready_steps, results):
                if isinstance(result, Exception):
                    state.mark_failed(f"Step {step.id} failed: {str(result)}")
                    WorkflowEventPublisher.emit("WorkflowFailed", state.execution_id, self.tenant_id, {"failed_step": step.id, "error": str(result)})
                    break
                else:
                    state.completed_steps.append(step.id)
                    del remaining_steps[step.id]
                    
        if state.status == "running":
            state.mark_completed()
            WorkflowEventPublisher.emit("WorkflowCompleted", state.execution_id, self.tenant_id, {"completed_steps": len(state.completed_steps)})

    async def _execute_step(self, state: WorkflowExecutionState, step: WorkflowStepDefinition) -> Any:
        """Executes a single step, mapping inputs from the shared context."""
        state.current_step = step.id
        WorkflowEventPublisher.emit("StepStarted", state.execution_id, self.tenant_id, {"step_id": step.id, "agent": step.agent})
        
        if step.requires_approval:
            # In a real system, this would transition to "paused" and await a callback.
            WorkflowEventPublisher.emit("WaitingForApproval", state.execution_id, self.tenant_id, {"step_id": step.id})
            # We simulate approval for this local execution
            
        AgentClass = AGENT_REGISTRY.get(step.agent)
        if not AgentClass:
            raise ValueError(f"Unknown agent: {step.agent}")
            
        agent = AgentClass(tenant_id=self.tenant_id, user_id=self.user_id)
        method = getattr(agent, step.action, None)
        if not method:
            raise ValueError(f"Agent {step.agent} has no method {step.action}")

        # Map inputs
        resolved_inputs = {}
        for k, v in step.inputs.items():
            if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                # Very simple context variable resolution (e.g. {{artifacts.url}})
                path = v[2:-2].strip().split(".")
                val = state.context.model_dump()
                try:
                    for p in path:
                        val = val[p]
                    resolved_inputs[k] = val
                except KeyError:
                    resolved_inputs[k] = None
            else:
                resolved_inputs[k] = v

        retries = step.retries
        last_err = None
        for attempt in range(retries + 1):
            try:
                result = await method(**resolved_inputs)
                # Store result in step_outputs and artifacts
                state.context.step_outputs[step.id] = result
                # Merge dict outputs into graph artifacts
                if isinstance(result, dict):
                    state.context.artifacts.update(result)
                WorkflowEventPublisher.emit("StepCompleted", state.execution_id, self.tenant_id, {"step_id": step.id, "attempt": attempt+1})
                return result
            except Exception as e:
                last_err = e
                WorkflowEventPublisher.emit("StepFailed", state.execution_id, self.tenant_id, {"step_id": step.id, "attempt": attempt+1, "error": str(e)})
        
        raise last_err
