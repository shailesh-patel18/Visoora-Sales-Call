import structlog
from typing import List, Optional
from v2.domain.crm.models import Lead, LeadStatus
from v2.domain.crm.repository import lead_repository
from v2.foundation.events.memory_adapter import event_bus
from v2.foundation.events.bus import BaseDomainEvent

logger = structlog.get_logger("lead_service")

class LeadCreatedEvent(BaseDomainEvent):
    event_name: str = "LeadCreated"

class LeadService:
    """
    Business logic layer for Leads.
    Enforces rules like deduplication and scoring before interacting with the Repository.
    """
    
    @staticmethod
    async def process_new_prospect(tenant_id: str, prospect_data: dict) -> Optional[Lead]:
        """
        Called by the ProspectingAgent.
        Validates, deduplicates, and creates a new Lead.
        """
        email = prospect_data.get("email")
        
        # 1. Deduplication Logic (Stubbed)
        # In a real system, we'd query the DB by email/linkedin_url
        is_duplicate = False 
        
        if is_duplicate:
            logger.info("duplicate_lead_rejected", email=email)
            return None
            
        # 2. Validation & Model Creation
        try:
            new_lead = Lead(
                tenant_id=tenant_id,
                first_name=prospect_data.get("first_name", "Unknown"),
                last_name=prospect_data.get("last_name", ""),
                email=email,
                company_name=prospect_data.get("company_name", "Unknown"),
                status=LeadStatus.NEW
            )
            
            # 3. Save to Repository
            saved_lead = await lead_repository.save(new_lead)
            
            # 4. Emit Domain Event
            evt = LeadCreatedEvent(
                tenant_id=tenant_id,
                trace_id="system",
                payload={"lead_id": saved_lead.id, "email": email}
            )
            await event_bus.publish(evt)
            
            return saved_lead
            
        except Exception as e:
            logger.error("lead_creation_failed", error=str(e), data=prospect_data)
            return None
