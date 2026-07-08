from typing import Optional, List
import structlog
from v2.domain.crm.models import Lead, LeadStatus

logger = structlog.get_logger("crm_lead_repository")

class MemoryLeadAdapter:
    def __init__(self):
        self._leads = {}
        # Pre-seed for testing (Phase 4 mock data)
        for i in range(1, 15):
            mock_id = f"test-lead-{i}"
            self._leads[mock_id] = Lead(
                id=mock_id,
                tenant_id="test-tenant",
                first_name=f"John{i}",
                last_name="Doe",
                company_name=f"Acme Corp {i}",
                status=LeadStatus.QUALIFIED
            )
        
    async def save(self, lead: Lead) -> Lead:
        self._leads[lead.id] = lead
        logger.info("lead_saved", lead_id=lead.id, status=lead.status.value)
        return lead
        
    async def get(self, lead_id: str) -> Optional[Lead]:
        return self._leads.get(lead_id)
        
    async def get_by_tenant(self, tenant_id: str) -> List[Lead]:
        # Return all for testing mock data
        return list(self._leads.values())

# Global Instance for DI
lead_repository = MemoryLeadAdapter()
