import logging
import asyncio
from typing import Dict, Any
from ..events.models import MissionCompleted, MissionEvaluated
from ..events.bus import global_event_bus

logger = logging.getLogger(__name__)

class MissionEvaluator:
    """
    Subscribes to MissionCompleted events and grades the output.
    """
    def __init__(self):
        pass
        
    async def evaluate_mission(self, event: MissionCompleted):
        logger.info(f"MissionEvaluator: Starting evaluation for mission {event.mission_id}")
        
        final_state = event.payload.get("final_state", {})
        
        # Determine some heuristic or LLM-based scores based on the final_state.
        # For this MVP, we use deterministic heuristics on the state.
        
        # Multi-dimensional Evaluation Rubric
        scores = {
            "website_analysis": 0.0,
            "lead_quality": 0.0,
            "personalization": 0.0,
            "groundedness": 10.0, # Default high
            "hallucination_pct": 0.0,
            "task_completion": 0.0,
            "cost_efficiency": 10.0,
            "latency_score": 10.0,
            "tool_usage": 10.0,
            "overall": 0.0
        }
        
        # 1. Lead Quality
        leads = final_state.get("decision_makers", [])
        emails = [l.get("email") for l in leads if l.get("email")]
        scores["lead_quality"] = min(len(emails) * 2.0, 10.0)
        
        # 2. Website Analysis
        website = final_state.get("website_summary")
        if website: scores["website_analysis"] = 10.0
        
        # 3. Personalization
        drafts = final_state.get("outreach_drafts", [])
        if drafts: scores["personalization"] = 9.0
        
        # 4. Task Completion
        scores["task_completion"] = (scores["lead_quality"] + scores["website_analysis"] + scores["personalization"]) / 3.0
        
        # 5. Overall
        scores["overall"] = (scores["task_completion"] + scores["groundedness"] + scores["cost_efficiency"]) / 3.0
        
        # Simulate LLM delay
        await asyncio.sleep(0.5)
        
        logger.info(f"MissionEvaluator: Mission {event.mission_id} scored: {scores}")
        
        # Emit event
        global_event_bus.publish(MissionEvaluated(event.mission_id, scores))

evaluator = MissionEvaluator()

def register_evaluator():
    global_event_bus.subscribe("MissionCompleted", evaluator.evaluate_mission)
    logger.info("Registered MissionEvaluator to EventBus")
