from typing import List
import structlog
from v2.domain.crm.models import Lead, LeadStatus
from server.storage_manager import supabase_client

logger = structlog.get_logger("legacy_crm_adapter")

class LegacyCRMAdapter:
    """
    Adapter to read legacy prospects from the v1 database and map them
    to the v2 Lead Domain Model. 
    """
    
    @staticmethod
    async def fetch_legacy_leads(tenant_id: str) -> List[Lead]:
        if not supabase_client:
            return []
            
        try:
            # Assuming MVP stored leads in a generic 'prospects' table or within workflows
            # We map whatever that old structure was into the strict v2 Lead
            res = supabase_client.table("workflow_jobs")\
                .select("payload, status")\
                .eq("tenant_id", tenant_id)\
                .eq("workflow_type", "prospecting")\
                .execute()
                
            legacy_leads = []
            if res.data:
                for job in res.data:
                    prospects = job.get("payload", {}).get("found_prospects", [])
                    for p in prospects:
                        lead = Lead(
                            tenant_id=tenant_id,
                            first_name=p.get("name", "").split(" ")[0] if p.get("name") else "Unknown",
                            last_name=p.get("name", "").split(" ")[-1] if p.get("name") else "",
                            company_name=p.get("company", "Unknown"),
                            email=p.get("email"),
                            status=LeadStatus.NEW if job.get("status") != "completed" else LeadStatus.CONTACTED
                        )
                        legacy_leads.append(lead)
                        
            logger.info("legacy_leads_adapted", count=len(legacy_leads), tenant_id=tenant_id)
            return legacy_leads
            
        except Exception as e:
            logger.error("legacy_crm_adapter_failed", tenant_id=tenant_id, error=str(e))
            return []
