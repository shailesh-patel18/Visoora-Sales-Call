import uuid
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import structlog
from v2.foundation.context.middleware import get_platform_context

logger = structlog.get_logger("artifact_store")

class AIArtifact(BaseModel):
    """
    First-class entity representing anything an AI produces.
    Can be reused, embedded, or versioned.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    artifact_type: str  # e.g., "WebsiteAudit", "EmailDraft", "VoiceScript"
    content: Dict[str, Any]
    
    # Metadata
    version: int = 1
    mission_id: Optional[str] = None
    agent_id: Optional[str] = None
    prompt_version: Optional[str] = None
    model_used: Optional[str] = None
    
    # Governance
    quality_score: Optional[float] = None
    status: str = "draft" # draft, approved, rejected, archived
    
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class IArtifactRepository(ABC):
    @abstractmethod
    async def save(self, artifact: AIArtifact) -> AIArtifact:
        pass
        
    @abstractmethod
    async def get(self, artifact_id: str) -> Optional[AIArtifact]:
        pass


class MemoryArtifactAdapter(IArtifactRepository):
    def __init__(self):
        self._artifacts = {}
        
    async def save(self, artifact: AIArtifact) -> AIArtifact:
        ctx = get_platform_context()
        trace_id = ctx.trace_id if ctx else "unknown"
        
        self._artifacts[artifact.id] = artifact
        logger.info("artifact_saved", artifact_id=artifact.id, type=artifact.artifact_type, trace_id=trace_id)
        return artifact
        
    async def get(self, artifact_id: str) -> Optional[AIArtifact]:
        return self._artifacts.get(artifact_id)

# Global Instance for DI
artifact_store = MemoryArtifactAdapter()
