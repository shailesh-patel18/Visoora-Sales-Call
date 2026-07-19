import httpx
import logging
from typing import List, Dict, Any
from .provider import ProspectProvider
from .capability import PeopleDiscoveryCapability, CompanyDiscoveryCapability

logger = logging.getLogger(__name__)

import time

class ApolloProvider(ProspectProvider, PeopleDiscoveryCapability, CompanyDiscoveryCapability):
    """
    Provider for Apollo API integration.
    Handles searching people via the /v1/mixed_people/search endpoint.
    """

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.cost = 0.05 # Paid provider
        
        from .registry import global_capability_registry
        global_capability_registry.register(self)

    @property
    def name(self) -> str:
        return "Apollo"

    async def research_company(self, company_name: str) -> Dict[str, Any]:
        """
        Placeholder for Apollo company research capability.
        """
        start_time = time.time()
        self.report_metric(True, (time.time() - start_time) * 1000)
        return {"description": f"{company_name} (Apollo Company Placeholder)"}

    async def find_leads(self, icp_segment: str, limit: int = 5) -> List[Dict[str, Any]]:
        start_time = time.time()
        if not self.api_key:
            logger.warning("ApolloProvider: Missing API key")
            self.report_metric(False, (time.time() - start_time) * 1000)
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.apollo.io/v1/mixed_people/search",
                    headers={
                        "Cache-Control": "no-cache", 
                        "Content-Type": "application/json",
                        "X-Api-Key": self.api_key
                    },
                    json={
                        "q_keywords": icp_segment,
                        "per_page": limit
                    }
                )

                if resp.status_code == 403:
                    logger.warning(f"ApolloProvider: 403 Forbidden (Likely free tier limitation) - {resp.text}")
                    self.report_metric(False, (time.time() - start_time) * 1000)
                    return []
                elif resp.status_code != 200:
                    logger.warning(f"ApolloProvider: API returned status {resp.status_code} - {resp.text}")
                    self.report_metric(False, (time.time() - start_time) * 1000)
                    return []

                data = resp.json()
                people = data.get("people", [])
                
                leads = []
                for p in people:
                    leads.append({
                        "name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                        "company": p.get("organization", {}).get("name", "Unknown"),
                        "title": p.get("title", "Unknown"),
                        "email": p.get("email", "Unknown")
                    })
                
                self.report_metric(True, (time.time() - start_time) * 1000)
                return leads

        except Exception as e:
            logger.error(f"ApolloProvider: Exception during search - {e}")
            self.report_metric(False, (time.time() - start_time) * 1000)
            return []
