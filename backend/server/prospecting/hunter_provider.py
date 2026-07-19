from typing import List
from .provider import ProspectProvider
from .capability import EmailFinderCapability

class HunterProvider(ProspectProvider, EmailFinderCapability):
    def __init__(self, api_key: str = ""):
        super().__init__()
        self.api_key = api_key
        self.cost = 0.02 # Paid
        
        from .registry import global_capability_registry
        global_capability_registry.register(self)

    @property
    def name(self) -> str:
        return "Hunter"

    async def find_emails(self, name: str, company_domain: str) -> List[str]:
        """
        Mock implementation of Hunter email finding.
        """
        import time
        start_time = time.time()
        # In a real scenario, this would query the Hunter API.
        result = [f"{name.lower().replace(' ', '.')}@{company_domain}"]
        self.report_metric(True, (time.time() - start_time) * 1000)
        return result
