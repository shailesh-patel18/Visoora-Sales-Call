from typing import List
from v2.agents.base_agent import BaseAgent
from v2.ai.capability_router import AICapability
from v2.ai.tool_registry import ToolCapability

class ProspectingAgent(BaseAgent):
    """
    Business Application Agent: Responsible for identifying qualified leads
    that match the Ideal Customer Profile (ICP) found in the Business Brain.
    """
    
    @property
    def system_prompt(self) -> str:
        return """
        You are a highly analytical Lead Generation Expert.
        Given an Ideal Customer Profile (ICP), use your tools to find 
        companies and decision-makers that perfectly match the criteria.
        Ensure you only return highly qualified leads.
        """
        
    @property
    def required_capabilities(self) -> List[AICapability]:
        # Needs to parse large JSON lists of leads and reason about fit
        return [AICapability.JSON_MODE, AICapability.TOOL_CALLING, AICapability.REASONING]
        
    @property
    def allowed_tools(self) -> List[ToolCapability]:
        return [ToolCapability.FIND_PROSPECTS]
        
    async def process_found_prospects(self, tenant_id: str, raw_prospects: List[dict]):
        """
        Called when the LLM returns the JSON list of qualified prospects.
        We route these directly into the strict Domain Layer, preventing AI hallucinations 
        from polluting the database.
        """
        from v2.domain.crm.service import LeadService
        
        saved_leads = []
        for prospect in raw_prospects:
            lead = await LeadService.process_new_prospect(tenant_id, prospect)
            if lead:
                saved_leads.append(lead)
                
        return saved_leads
