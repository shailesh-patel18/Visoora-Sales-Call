from typing import List
from v2.agents.base_agent import BaseAgent
from v2.ai.capability_router import AICapability
from v2.ai.tool_registry import ToolCapability

class VoiceAgent(BaseAgent):
    """
    Business Application Agent: Handles real-time conversational AI over the phone.
    """
    
    @property
    def system_prompt(self) -> str:
        return """
        You are an elite B2B Sales Representative making an outbound cold call.
        Keep your responses under 2 sentences. Be conversational, handle objections smoothly, 
        and aim to book a meeting.
        """
        
    @property
    def required_capabilities(self) -> List[AICapability]:
        # Needs high-speed streaming capabilities for real-time voice
        return [AICapability.STREAMING, AICapability.REASONING]
        
    @property
    def allowed_tools(self) -> List[ToolCapability]:
        # The Voice Agent doesn't *initiate* the call (the orchestrator does that),
        # but it might need to check calendars or book meetings mid-call.
        return [ToolCapability.BOOK_MEETING]
        
    async def process_voice_turn(self, tenant_id: str, lead_id: str, user_transcript: str) -> str:
        """
        Takes the user's spoken words and streams back the AI's response.
        """
        # In reality, this would maintain a websocket stream with the LLM Gateway
        return "That's a great point. How about we schedule a brief 10-minute demo on Tuesday to show you?"
