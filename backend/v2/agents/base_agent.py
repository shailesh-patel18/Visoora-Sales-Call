from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import structlog
from v2.agents.memory import IAgentMemory, ConversationMemory
from v2.ai.capability_router import AICapability
from v2.ai.llm_gateway import LLMGateway
from v2.ai.tool_registry import ToolCapability, tool_registry
from v2.ai.evaluation import track_evaluation
from v2.foundation.context.middleware import get_platform_context

logger = structlog.get_logger("base_agent")

class BaseAgent(ABC):
    """
    The Foundation v1.0 Base Agent.
    All future agents (ResearchAgent, VoiceAgent, ProspectingAgent) inherit from this.
    It standardizes execution loops, memory handling, and telemetry.
    """
    
    def __init__(self, agent_id: str, memory: Optional[IAgentMemory] = None):
        self.agent_id = agent_id
        self.memory = memory or ConversationMemory()
        
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The core instructions for this specific agent."""
        pass
        
    @property
    def required_capabilities(self) -> List[AICapability]:
        """Which AI capabilities this agent requires to function."""
        return [AICapability.FAST]
        
    @property
    def allowed_tools(self) -> List[ToolCapability]:
        """Which external tools this agent is authorized to use."""
        return []

    async def _execute_tool(self, tool_capability: ToolCapability, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Safely executes a tool if the agent is authorized."""
        if tool_capability not in self.allowed_tools:
            logger.warning("unauthorized_tool_access", agent_id=self.agent_id, tool=tool_capability.name)
            return {"error": "Unauthorized to use this tool"}
            
        return await tool_registry.execute(tool_capability, payload)

    @track_evaluation("agent_execution_loop")
    async def run(self, user_input: str) -> Dict[str, Any]:
        """
        The standardized execution loop.
        1. Store user input
        2. Call LLM Gateway
        3. Handle potential tool calls
        4. Reflect / Store result
        """
        ctx = get_platform_context()
        logger.info("agent_run_started", agent_id=self.agent_id, tenant_id=ctx.tenant_id if ctx else "none")
        
        self.memory.add_message("user", user_input)
        
        # In a real implementation, we would format the entire conversation history here.
        # For brevity, passing the latest input.
        try:
            response = await LLMGateway.generate(
                system_prompt=self.system_prompt,
                user_prompt=user_input,
                capabilities=self.required_capabilities
            )
            
            content = response.get("content", "")
            self.memory.add_message("assistant", content)
            
            logger.info("agent_run_completed", agent_id=self.agent_id)
            return {"status": "success", "response": content}
            
        except Exception as e:
            logger.error("agent_run_failed", agent_id=self.agent_id, error=str(e))
            raise
