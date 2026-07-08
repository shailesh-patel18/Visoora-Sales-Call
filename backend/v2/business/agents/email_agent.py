from typing import List, Dict, Any
from pydantic import BaseModel, Field
from v2.agents.base_agent import BaseAgent
from v2.ai.capability_router import AICapability
from v2.ai.tool_registry import ToolCapability
from v2.domain.crm.models import EmailDraft
from ai_platform.providers.openai_provider import OpenAIProvider
import structlog

logger = structlog.get_logger("email_agent")

class EmailDraftSchema(BaseModel):
    subject: str = Field(description="The subject line of the email")
    body: str = Field(description="The HTML or plain text body of the email")
    evidence_log: List[Dict[str, str]] = Field(description="A log of reasoning steps taken to generate this email. E.g. [{'step': 'Found recent news', 'detail': 'Company raised Series A'}]")

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
        the prospect's pain points and the value proposition defined in the context.
        Keep it under 100 words. Do not use generic buzzwords.
        Always explain your reasoning in the evidence_log.
        """
        
    @property
    def required_capabilities(self) -> List[AICapability]:
        return [AICapability.REASONING, AICapability.TOOL_CALLING]
        
    @property
    def allowed_tools(self) -> List[ToolCapability]:
        return [ToolCapability.SEND_EMAIL]

    async def draft_email(self, tenant_id: str, lead_id: str, prompt_context: str) -> EmailDraft:
        """
        Drafts the email using OpenAI structured output to enforce the evidence_log.
        """
        provider = OpenAIProvider(model_name="gpt-4o-mini") # Fast and cheap for drafting
        
        try:
            # We enforce structured JSON output to get the subject, body, and evidence_log cleanly.
            result: EmailDraftSchema = await provider.generate_structured(
                prompt=prompt_context,
                schema=EmailDraftSchema,
                system_prompt=self.system_prompt
            )
            
            draft = EmailDraft(
                tenant_id=tenant_id,
                lead_id=lead_id,
                subject=result.subject,
                body=result.body,
                evidence_log=result.evidence_log
            )
            return draft
            
        except Exception as e:
            logger.error("draft_email_failed", error=str(e), lead_id=lead_id)
            # Fallback draft if AI fails
            return EmailDraft(
                tenant_id=tenant_id,
                lead_id=lead_id,
                subject="Quick Question",
                body="We noticed your recent growth and would love to connect.",
                evidence_log=[{"step": "Error", "detail": "AI generation failed, used fallback."}]
            )
