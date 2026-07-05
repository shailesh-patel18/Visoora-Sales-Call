from typing import Optional, Dict, Any
import structlog
from v2.knowledge.brain_models import BusinessBrain, IdealCustomerProfile, ObjectionHandling
from server.storage_manager import supabase_client

logger = structlog.get_logger("legacy_brain_adapter")

class LegacyBrainAdapter:
    """
    Adapter to read unstructured JSON blob data from the legacy MVP database
    and parse it into the strict v2 Pydantic BusinessBrain models.
    """
    
    @staticmethod
    async def fetch_and_parse(tenant_id: str) -> Optional[BusinessBrain]:
        if not supabase_client:
            logger.warning("legacy_db_not_configured")
            return None
            
        try:
            # Legacy MVP used domain/tenant interchangeably in some spots, 
            # assuming tenant_id maps to domain or an identifier in the old table.
            res = supabase_client.table("business_brains")\
                .select("*")\
                .eq("tenant_id", tenant_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
                
            if not res.data:
                return None
                
            legacy_record = res.data[0]
            metadata = legacy_record.get("metadata", {})
            full_report = metadata.get("full_report", {})
            
            # Map unstructured data to strict v2 models
            icp = IdealCustomerProfile(
                titles=full_report.get("target_titles", []),
                industries=full_report.get("target_industries", []),
                company_size=full_report.get("company_size", "Unknown"),
                pain_points=full_report.get("pain_points", [])
            )
            
            objections = ObjectionHandling(
                common_objections=[
                    {"trigger": obj.get("objection"), "rebuttal": obj.get("rebuttal")}
                    for obj in full_report.get("objections", [])
                    if isinstance(obj, dict)
                ]
            )
            
            brain = BusinessBrain(
                tenant_id=tenant_id,
                domain=legacy_record.get("domain", ""),
                company_name=full_report.get("company_name", "Unknown"),
                value_proposition=full_report.get("value_proposition", "Unknown"),
                icp=icp,
                objections=objections,
                version=1
            )
            
            logger.info("legacy_brain_adapted", tenant_id=tenant_id)
            return brain
            
        except Exception as e:
            logger.error("legacy_brain_adapter_failed", tenant_id=tenant_id, error=str(e))
            return None
