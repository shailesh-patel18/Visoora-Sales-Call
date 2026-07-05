from typing import Optional
from pydantic import BaseModel
from .base_agent import BaseAgent
from ..prompts.registry import prompt_registry
from ..schemas import PromptSchema, Capability

class LeadScoreResult(BaseModel):
    score_adjustment: int
    reasoning: str
    similar_customers_count: int
    confidence_score: int
    citations: list[str]

class ProspectingAgent(BaseAgent):
    """
    Agent responsible for lead scoring and prospecting.
    """
    
    async def score_lead(self, context_str: str) -> LeadScoreResult:
        prompt_id = "lead_score_v1"
        if not prompt_registry.get_prompt(prompt_id):
            prompt_registry._prompts[prompt_id] = PromptSchema(
                id=prompt_id,
                version=1,
                description="Score a lead based on ICP.",
                system_instruction="You are an expert lead scorer. Output a score from 0 to 100.",
                supported_capabilities=[Capability.JSON_SCHEMA, Capability.REASONING]
            )
            
        result = await self.execute_task(
            task_name="score_lead",
            prompt_id=prompt_id,
            context=context_str,
            schema=LeadScoreResult
        )
        return result
