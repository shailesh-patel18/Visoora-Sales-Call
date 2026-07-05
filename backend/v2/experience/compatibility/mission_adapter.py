import structlog
from typing import Dict, Any
from v2.mission.models import Mission
from v2.mission.repository import mission_repository
from v2.workflow.engine import WorkflowEngine
from v2.workflow.models import WorkflowDefinition
import json

logger = structlog.get_logger("legacy_mission_adapter")

class LegacyMissionAdapter:
    """
    Adapter to translate legacy "Start Campaign" API requests into 
    v2 Mission and Workflow Engine initializations.
    """
    
    @staticmethod
    async def start_legacy_campaign_as_mission(tenant_id: str, campaign_name: str, payload: Dict[str, Any]) -> str:
        """
        Takes a legacy campaign request, creates a v2 Mission, and wires it to the declarative workflow.
        Returns the v2 Mission ID.
        """
        logger.info("translating_legacy_campaign", tenant_id=tenant_id, campaign_name=campaign_name)
        
        # 1. Create the Mission Objective
        mission = Mission(
            tenant_id=tenant_id,
            name=campaign_name,
            goal_description=payload.get("instruction", "Execute autonomous outbound campaign")
        )
        
        # 2. Load the declarative workflow
        try:
            with open("v2/business/workflows/outbound_campaign.json", "r") as f:
                workflow_data = json.load(f)
            definition = WorkflowDefinition(**workflow_data)
        except Exception as e:
            logger.error("failed_to_load_workflow", error=str(e))
            raise e
            
        # 3. Initialize Workflow Execution State
        state = await WorkflowEngine.initialize(tenant_id, definition, payload)
        
        # 4. Bind workflow to Mission
        mission.active_workflows.append(state.execution_id)
        await mission_repository.save(mission)
        
        # 5. Kick off Orchestrator (in reality this would be done by an async worker via EventBus)
        from v2.mission.orchestrator import MissionOrchestrator
        import asyncio
        asyncio.create_task(MissionOrchestrator.dispatch_executable_steps(mission.id))
        
        return mission.id
