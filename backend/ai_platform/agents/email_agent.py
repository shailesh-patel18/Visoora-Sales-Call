from typing import Optional, Any
from .base_agent import BaseAgent
from ..prompts.registry import prompt_registry
from ..schemas import PromptSchema, Capability
from pydantic import BaseModel

class EmailDraft(BaseModel):
    subject: str
    body: str

class EmailAgent(BaseAgent):
    """
    Agent responsible for drafting emails.
    """
    
    async def draft_email(self, context_str: str, memory: Optional[Any] = None) -> EmailDraft:
        prompt_id = "email_draft_v1"
        if not prompt_registry.get_prompt(prompt_id):
            prompt_registry._prompts[prompt_id] = PromptSchema(
                id=prompt_id,
                version=1,
                description="Draft an email based on context.",
                system_instruction="You are an expert sales copywriter. Draft a cold email.",
                supported_capabilities=[Capability.JSON_SCHEMA, Capability.FAST]
            )
            
        result = await self.execute_task(
            task_name="draft_email",
            prompt_id=prompt_id,
            context=context_str,
            schema=EmailDraft,
            memory=memory
        )
        return result
