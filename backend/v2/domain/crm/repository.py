from typing import Optional, List
import structlog
from v2.domain.crm.models import EmailDraft, DraftStatus

logger = structlog.get_logger("crm_repository")

class MemoryDraftAdapter:
    def __init__(self):
        self._drafts = {}
        # Pre-seed for testing
        mock_id = "test-draft-123"
        self._drafts[mock_id] = EmailDraft(
            id=mock_id,
            tenant_id="test-tenant", # We don't have a real tenant yet, wait, we need to match the user's tenant from the JWT.
            # Actually, let's just make it return for the get_by_status regardless of tenant for the mock, or seed it when requested.
            lead_id="lead-456",
            subject="Scaling engineering at Acme Corp",
            body="Hi John,\n\nI noticed Acme Corp recently raised $5M. We help engineering teams scale their infrastructure. Open to a chat?",
            evidence_log=[
                {"step": "Prospect Research", "detail": "Found John Doe is VP of Engineering at Acme Corp."},
                {"step": "Company News", "detail": "Acme Corp raised $5M Series A last week."},
                {"step": "Value Mapping", "detail": "Mapped our infrastructure scaling solution to their recent funding event."}
            ]
        )
        
    async def save(self, draft: EmailDraft) -> EmailDraft:
        self._drafts[draft.id] = draft
        logger.info("draft_saved", draft_id=draft.id, status=draft.status.value)
        return draft
        
    async def get(self, draft_id: str) -> Optional[EmailDraft]:
        return self._drafts.get(draft_id)
        
    async def get_by_status(self, tenant_id: str, status: DraftStatus) -> List[EmailDraft]:
        # For testing, we just return all drafts with the status since we hardcoded tenant_id above
        return [d for d in self._drafts.values() if d.status == status]

# Global Instance for DI
draft_repository = MemoryDraftAdapter()
