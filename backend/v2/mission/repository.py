from abc import ABC, abstractmethod
from typing import Optional, List
import structlog
from v2.mission.models import Mission
from v2.foundation.context.middleware import get_platform_context

logger = structlog.get_logger("mission_repository")

class IMissionRepository(ABC):
    @abstractmethod
    async def save(self, mission: Mission) -> Mission:
        pass
        
    @abstractmethod
    async def get(self, mission_id: str) -> Optional[Mission]:
        pass
        
    @abstractmethod
    async def get_active_by_tenant(self, tenant_id: str) -> List[Mission]:
        pass

class MemoryMissionAdapter(IMissionRepository):
    def __init__(self):
        self._missions = {}
        
    async def save(self, mission: Mission) -> Mission:
        ctx = get_platform_context()
        trace_id = ctx.trace_id if ctx else "unknown"
        
        self._missions[mission.id] = mission
        logger.info("mission_saved", mission_id=mission.id, status=mission.status.value, trace_id=trace_id)
        return mission
        
    async def get(self, mission_id: str) -> Optional[Mission]:
        return self._missions.get(mission_id)
        
    async def get_active_by_tenant(self, tenant_id: str) -> List[Mission]:
        return [m for m in self._missions.values() if m.tenant_id == tenant_id and m.status == "active"]

# Global Instance for DI
mission_repository = MemoryMissionAdapter()
