from typing import List, Dict, Any
import structlog
from .base import BaseProspectProvider
from server.storage_manager import supabase_admin_client as supabase_client

logger = structlog.get_logger("db_prospect_provider")

class DBProspectProvider(BaseProspectProvider):
    """
    Legacy provider that fetches pre-loaded contacts from the Supabase contacts table.
    Used as a fallback or for sandbox testing.
    """
    
    async def search_prospects(self, tenant_id: str, business_brain: Dict[str, Any], max_results: int = 5) -> List[Dict[str, Any]]:
        if not supabase_client:
            return self._mock_fallback()
            
        try:
            # We first try to fetch from the general contacts table
            res = supabase_client.table("contacts").select("*").eq("tenant_id", tenant_id).limit(max_results).execute()
            if res.data:
                return res.data
                
            # Fallback to older crm_contacts if available
            res = supabase_client.table("crm_contacts").select("*").eq("tenant_id", tenant_id).limit(max_results).execute()
            if res.data:
                return res.data
                
            return self._mock_fallback()
        except Exception as e:
            logger.error("db_prospect_provider_fetch_failed", error=str(e))
            return self._mock_fallback()

    def _mock_fallback(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "mock_apollo_1", 
                "company": "Acme Healthcare", 
                "first_name": "John", 
                "last_name": "Smith", 
                "title": "CEO",
                "email": "john.smith@acme-healthcare.example.com"
            }
        ]
