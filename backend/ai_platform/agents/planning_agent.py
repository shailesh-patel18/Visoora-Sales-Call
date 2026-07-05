import structlog
import asyncio
from typing import Dict, Any, List
from server.services.mission_engine import Mission, MissionTask, add_mission_task

logger = structlog.get_logger("planning_agent")

class PlanningAgent:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    async def generate_mission_plan(self, mission_id: str, goal: str, business_brain: Dict[str, Any]) -> List[MissionTask]:
        """
        Takes a high-level goal and Business Brain, and returns a DAG of MissionTasks.
        For Phase 3 MVP, we will use a static template based on the goal, but in the future
        this would be a prompt to an LLM to dynamically generate the execution graph.
        """
        logger.info("planning_mission_start", mission_id=mission_id, goal=goal)
        
        tasks = []
        
        if "outreach" in goal.lower() or "campaign" in goal.lower() or "customers" in goal.lower():
            # Standard Outbound DAG
            
            # 1. Prospecting
            prospecting = add_mission_task(
                mission_id=mission_id,
                agent_type="prospecting_agent",
                dependencies=[],
                payload={"icp": business_brain.get("icp", []), "target_count": 5}
            )
            tasks.append(prospecting)
            
            # 2. Research (depends on Prospecting)
            research = add_mission_task(
                mission_id=mission_id,
                agent_type="research_agent",
                dependencies=[prospecting.id],
                payload={"depth": "deep"}
            )
            tasks.append(research)
            
            # 3. Email Draft (depends on Research)
            email = add_mission_task(
                mission_id=mission_id,
                agent_type="email_agent",
                dependencies=[research.id],
                payload={"goal": goal, "value_props": business_brain.get("products", [])}
            )
            tasks.append(email)
            
            # 4. Voice Script (depends on Research & Email)
            voice = add_mission_task(
                mission_id=mission_id,
                agent_type="voice_agent",
                dependencies=[research.id, email.id],
                payload={"objections": business_brain.get("pain_points", [])}
            )
            tasks.append(voice)
            
        else:
            # Fallback simple DAG
            research = add_mission_task(
                mission_id=mission_id,
                agent_type="research_agent",
                dependencies=[],
                payload={"goal": goal}
            )
            tasks.append(research)
            
        logger.info("planning_mission_complete", mission_id=mission_id, task_count=len(tasks))
        return tasks
