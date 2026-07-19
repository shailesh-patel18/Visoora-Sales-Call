import logging
import time
from typing import List, Dict, Any
from .provider import ProspectProvider
from .capability import CompanyDiscoveryCapability, PeopleDiscoveryCapability, EmailFinderCapability

logger = logging.getLogger(__name__)

class MockProvider(ProspectProvider, CompanyDiscoveryCapability, PeopleDiscoveryCapability, EmailFinderCapability):
    """
    Dummy provider that always returns realistic mock data.
    Perfect for local development and free-tier testing.
    """

    def __init__(self):
        super().__init__()
        self.cost = 0.0 # Free
        
        from .registry import global_capability_registry
        global_capability_registry.register(self)

    @property
    def name(self) -> str:
        return "Mock"

    async def find_leads(self, icp_segment: str, limit: int = 5) -> List[Dict[str, Any]]:
        start_time = time.time()
        logger.info(f"MockProvider searching leads for segment: {icp_segment}")
        
        # Return realistic dummy leads
        mock_leads = [
            {"name": "Sarah Connor", "company": "Cyberdyne Systems", "title": "Director of IT", "email": "sarah@cyberdyne.mock"},
            {"name": "Tony Stark", "company": "Stark Industries", "title": "CEO", "email": "tony@stark.mock"},
            {"name": "Elena Fisher", "company": "Naughty Dog Media", "title": "VP of Engineering", "email": "elena@naughty.mock"},
            {"name": "Gordon Freeman", "company": "Black Mesa Research", "title": "Head Scientist", "email": "gordon@blackmesa.mock"},
            {"name": "Ellen Ripley", "company": "Weyland-Yutani Corp", "title": "Operations Manager", "email": "ellen@weyland.mock"}
        ]
        
        self.report_metric(True, (time.time() - start_time) * 1000)
        # Ensure we only return up to `limit` leads
        return mock_leads[:limit]

    async def find_emails(self, name: str, company_domain: str) -> List[str]:
        start_time = time.time()
        self.report_metric(True, (time.time() - start_time) * 1000)
        return [f"{name.lower().replace(' ', '.')}@{company_domain}"]

    async def research_company(self, company_name: str) -> Dict[str, Any]:
        start_time = time.time()
        self.report_metric(True, (time.time() - start_time) * 1000)
        return {
            "description": f"{company_name} is a leading B2B SaaS company.",
            "pain_points": ["Customer retention", "Lead conversion"],
            "technologies": ["React", "FastAPI"]
        }
