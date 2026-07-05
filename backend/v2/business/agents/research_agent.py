from typing import List
from v2.agents.base_agent import BaseAgent
from v2.ai.capability_router import AICapability
from v2.ai.tool_registry import ToolCapability

class ResearchAgent(BaseAgent):
    """
    Business Application Agent: Responsible for analyzing a target company's website
    and extracting value props, pain points, and competitors to populate the Business Brain.
    """
    
    @property
    def system_prompt(self) -> str:
        return """
        You are an elite B2B Sales Researcher.
        Your job is to analyze a company and extract their core value proposition,
        the main problems they solve, and their likely ideal customer profile (ICP).
        Use the READ_WEBSITE tool if you are given a URL.
        """
        
    @property
    def required_capabilities(self) -> List[AICapability]:
        # Needs reasoning to infer ICP, and tool calling to use web scrapers
        return [AICapability.REASONING, AICapability.TOOL_CALLING]
        
    @property
    def allowed_tools(self) -> List[ToolCapability]:
        return [ToolCapability.READ_WEBSITE, ToolCapability.SEARCH_COMPANY]
