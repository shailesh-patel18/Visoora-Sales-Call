import os
import httpx
import structlog
from typing import List, Dict, Any
from .base import BaseProspectProvider

logger = structlog.get_logger("apollo_prospect_provider")

class ApolloProspectProvider(BaseProspectProvider):
    """
    Fetches real prospects from Apollo.io using their API.
    Maps Apollo results into Visoora standard contact objects.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/v1"

    async def search_prospects(self, tenant_id: str, business_brain: Dict[str, Any], max_results: int = 5) -> List[Dict[str, Any]]:
        # Use business brain to construct search query
        # Example: we extract target titles or industries. If empty, use defaults.
        target_titles = business_brain.get("target_titles", ["CEO", "Founder", "VP Sales"])
        
        payload = {
            "api_key": self.api_key,
            "q_organization_domains": "", # Can add competitors if we want to extract their talent, or leave empty
            "person_titles": target_titles,
            "page": 1,
            "per_page": max_results
        }
        
        # Optional: Add industries if present
        industries = business_brain.get("icp_industries", [])
        if industries:
            payload["organization_industry_tag_ids"] = industries
            
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{self.base_url}/mixed_people/search", json=payload, timeout=10.0)
                
                if res.status_code == 200:
                    data = res.json()
                    people = data.get("people", [])
                    return self._map_apollo_to_visoora(people)
                else:
                    logger.error("apollo_api_error", status_code=res.status_code, response=res.text)
                    return []
        except Exception as e:
            logger.error("apollo_provider_exception", error=str(e))
            return []
            
    def _map_apollo_to_visoora(self, apollo_people: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        visoora_contacts = []
        for p in apollo_people:
            org = p.get("organization") or {}
            visoora_contacts.append({
                "id": f"apollo_{p.get('id')}",
                "first_name": p.get("first_name", ""),
                "last_name": p.get("last_name", ""),
                "title": p.get("title", ""),
                "email": p.get("email", ""),
                "company": org.get("name", "Unknown"),
                "website": org.get("website_url", ""),
                "linkedin_url": p.get("linkedin_url", ""),
                "source": "apollo"
            })
        return visoora_contacts
