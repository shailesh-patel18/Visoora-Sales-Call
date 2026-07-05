from typing import List
from v2.agents.base_agent import BaseAgent
from v2.ai.capability_router import AICapability
from v2.ai.tool_registry import ToolCapability
from v2.domain.crm.models import EmailDraft

class EmailAgent(BaseAgent):
    """
    Business Application Agent: Responsible for drafting hyper-personalized 
    outbound emails using context from the Business Brain and Lead data.
    """
    
    @property
    def system_prompt(self) -> str:
        return """
        You are an elite B2B Sales Copywriter.
        Your job is to write short, highly personalized cold emails that focus on 
        the prospect's pain points and the value proposition defined in the Business Brain.
        Keep it under 100 words. Do not use generic buzzwords.
        """
        
    @property
    def required_capabilities(self) -> List[AICapability]:
        # Needs reasoning to map value prop to pain points, and tool calling to send
        return [AICapability.REASONING, AICapability.TOOL_CALLING]
        
    @property
    def allowed_tools(self) -> List[ToolCapability]:
        return [ToolCapability.SEND_EMAIL]

    async def draft_email(self, tenant_id: str, lead_id: str, prompt_context: str) -> EmailDraft:
        """
        Drafts the email but routes it to the strict Domain Model (EmailDraft),
        meaning it requires Approval via the MissionOrchestrator before SEND_EMAIL is called.
        """
        # In reality, calls self._execute_with_llm(prompt_context)
        subject = "Drafted Subject: Quick Question"
        body = "Drafted Body: AI generated content based on " + prompt_context[:20]
        
        draft = EmailDraft(
            tenant_id=tenant_id,
            lead_id=lead_id,
            subject=subject,
            body=body
        )
        # Note: we would save this via an IEmailRepository in the domain layer.
        return draft
