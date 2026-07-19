from typing import List, Dict, Any
from .provider import ProspectProvider
from .capability import PeopleDiscoveryCapability

class LinkedInProvider(ProspectProvider, PeopleDiscoveryCapability):
    def __init__(self, api_key: str = ""):
        super().__init__()
        self.api_key = api_key
        self.cost = 0.05 # Paid
        
        from .registry import global_capability_registry
        global_capability_registry.register(self)

    @property
    def name(self) -> str:
        return "LinkedIn"

    async def find_leads(self, icp_segment: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Mock implementation of LinkedIn people search.
        """
        return []
