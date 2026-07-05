from abc import ABC, abstractmethod
from typing import Optional
import structlog
from v2.knowledge.brain_models import BusinessBrain
from v2.foundation.context.middleware import get_platform_context

logger = structlog.get_logger("brain_repository")

class IBusinessBrainRepository(ABC):
    """
    Port (Interface) for accessing the Business Brain.
    Ensures that domain logic doesn't depend on Supabase directly.
    """
    
    @abstractmethod
    async def get_by_tenant(self, tenant_id: str) -> Optional[BusinessBrain]:
        pass
        
    @abstractmethod
    async def save(self, brain: BusinessBrain) -> BusinessBrain:
        pass


class MemoryBrainAdapter(IBusinessBrainRepository):
    """
    In-memory adapter for local testing and development.
    """
    def __init__(self):
        self._brains = {}
        
    async def get_latest_for_tenant(self, tenant_id: str) -> Optional[BusinessBrain]:
        # 1. Try to fetch from v2 storage first
        v2_brain = self._brains.get(tenant_id)
        if v2_brain:
            return v2_brain
            
        # 2. Lazy Migration: Fallback to Legacy Adapter
        try:
            from v2.experience.compatibility.brain_adapter import LegacyBrainAdapter
            legacy_brain = await LegacyBrainAdapter.fetch_and_parse(tenant_id)
            if legacy_brain:
                # Save it to v2 storage so subsequent reads hit step 1
                await self.save(legacy_brain)
                logger.info("lazy_migration_completed", tenant_id=tenant_id)
                return legacy_brain
        except ImportError:
            pass
            
        return None
        
    async def get_by_tenant(self, tenant_id: str) -> Optional[BusinessBrain]:
        ctx = get_platform_context()
        trace_id = ctx.trace_id if ctx else "unknown"
        logger.info("brain_fetched", tenant_id=tenant_id, trace_id=trace_id)
        return self._brains.get(tenant_id)
        
    async def save(self, brain: BusinessBrain) -> BusinessBrain:
        ctx = get_platform_context()
        trace_id = ctx.trace_id if ctx else "unknown"
        
        # Increment version on save
        if brain.tenant_id in self._brains:
            brain.version = self._brains[brain.tenant_id].version + 1
            
        self._brains[brain.tenant_id] = brain
        logger.info("brain_saved", tenant_id=brain.tenant_id, version=brain.version, trace_id=trace_id)
        return brain

# Global Instance for DI
brain_repository = MemoryBrainAdapter()
