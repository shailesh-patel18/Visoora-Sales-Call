import logging
from typing import Dict, Any
from .models import MissionRequest
from ..memory.mission import MissionMemory
from ..orchestration.planner import MissionPlanner

logger = logging.getLogger(__name__)

class VisooraRuntime:
    """
    The main SDK entrypoint to the Visoora AI Platform.
    Wraps all planning, execution, memory, and observability into a single interface.
    """
    
    @classmethod
    async def execute(cls, request: MissionRequest) -> Dict[str, Any]:
        """
        Executes a mission synchronously (waits for completion) and returns the final state.
        """
        logger.info(f"VisooraRuntime: Executing mission {request.mission_id} (type={request.type})")
        
        # 1. Initialize Memory
        memory = MissionMemory(request.mission_id, request.tenant_id)
        
        # 2. Check for resume
        is_resume = await memory.load()
        if request.resume and not is_resume:
            logger.warning(f"VisooraRuntime: Requested resume but mission {request.mission_id} not found. Starting fresh.")
            
        if not is_resume:
            # Seed parameters into memory for the planner to use
            for k, v in request.parameters.items():
                memory.set(f"param_{k}", v)
        else:
            memory.update_metadata("retry_count", memory.get("metadata").get("retry_count", 0) + 1)
                
        # 3. Plan and Execute
        # Map request.type to different planners
        if request.type == "AI_SDR":
            from ..missions.ai_sdr import AISDRMissionPlanner
            planner = AISDRMissionPlanner(memory)
        else:
            planner = MissionPlanner(memory)
        
        # We assume the planner knows how to extract param_company_name, etc.
        # In the future, planner execution will take the request directly.
        company_name = memory.get("param_company_name") or "Unknown Company"
        icp_segment = memory.get("param_icp_segment") or "B2B SaaS"
        
        final_state = await planner.execute_mission(icp_segment, company_name)
        
        logger.info(f"VisooraRuntime: Mission {request.mission_id} completed successfully.")
        return final_state

    @classmethod
    async def plan(cls, request: MissionRequest) -> Dict[str, Any]:
        """Returns the execution graph without running it."""
        memory = MissionMemory(request.mission_id, request.tenant_id)
        # Mocking plan return
        return {"nodes": ["CompanyDiscovery", "PeopleDiscovery", "EmailFinding", "ApprovalNode", "EmailDispatch"]}
        
    @classmethod
    async def resume(cls, request: MissionRequest, approval_granted: bool = True) -> Dict[str, Any]:
        """Resumes a paused mission, typically after approval."""
        from ..events.models import MissionResumed
        from ..events.bus import global_event_bus
        
        request.resume = True
        logger.info(f"VisooraRuntime: Resuming mission {request.mission_id}")
        global_event_bus.publish(MissionResumed(request.mission_id, approval_granted=approval_granted))
        return await cls.execute(request)
        
    @classmethod
    async def replay(cls, mission_id: str, new_request: MissionRequest) -> Dict[str, Any]:
        """Replays a past mission from the beginning."""
        return await cls.execute(new_request)
        
    @classmethod
    async def evaluate(cls, mission_id: str) -> Dict[str, Any]:
        """Manually triggers evaluation on a mission."""
        from ..events.models import MissionCompleted
        from ..evaluation.evaluator import evaluator
        # Mock fetching state
        mock_event = MissionCompleted(mission_id, {"decision_makers": [{"email": "test@test.com"}]})
        await evaluator.evaluate_mission(mock_event)
        return {"status": "Evaluation queued"}
        
    @classmethod
    def diff(cls, mission_id_a: str, mission_id_b: str) -> Dict[str, Any]:
        """Diffs two missions."""
        from ..observability.differ import MissionDiffer
        return MissionDiffer().compare(mission_id_a, mission_id_b)

# Global singleton
runtime = VisooraRuntime()
