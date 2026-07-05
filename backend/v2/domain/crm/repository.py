from abc import ABC, abstractmethod
from typing import Optional, List
import structlog
from v2.domain.crm.models import Lead, LeadStatus
from v2.foundation.context.middleware import get_platform_context

logger = structlog.get_logger("crm_repository")

class ILeadRepository(ABC):
    @abstractmethod
    async def save(self, lead: Lead) -> Lead:
        pass
        
    @abstractmethod
    async def get(self, lead_id: str) -> Optional[Lead]:
        pass
        
    @abstractmethod
    async def list_by_tenant_and_status(self, tenant_id: str, status: LeadStatus) -> List[Lead]:
        pass

class MemoryLeadAdapter(ILeadRepository):
    def __init__(self):
        self._leads = {}
        
    async def save(self, lead: Lead) -> Lead:
        ctx = get_platform_context()
        trace_id = ctx.trace_id if ctx else "unknown"
        
        self._leads[lead.id] = lead
        logger.info("lead_saved", lead_id=lead.id, status=lead.status.value, trace_id=trace_id)
        return lead
        
    async def get(self, lead_id: str) -> Optional[Lead]:
        return self._leads.get(lead_id)
        
    async def list_by_tenant_and_status(self, tenant_id: str, status: LeadStatus) -> List[Lead]:
        return [l for l in self._leads.values() if l.tenant_id == tenant_id and l.status == status]

# Global Instance for DI
lead_repository = MemoryLeadAdapter()
