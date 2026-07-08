from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from security.rbac import RoleChecker, UserPrincipal
from v2.domain.crm.models import EmailDraft, DraftStatus
from v2.domain.crm.repository import draft_repository
from notifications.resend_provider import ResendProvider

router = APIRouter(prefix="/drafts", tags=["Drafts"])
notification_provider = ResendProvider()

class DraftUpdateRequest(BaseModel):
    subject: str
    body: str

@router.get("", response_model=List[EmailDraft])
async def list_pending_drafts(user: UserPrincipal = Depends(RoleChecker(["admin", "agent"]))):
    """List all drafts pending approval for the current tenant."""
    tenant_id = user.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=403, detail="No tenant_id in token")
        
    return await draft_repository.get_by_status(tenant_id, DraftStatus.PENDING_APPROVAL)

@router.put("/{draft_id}", response_model=EmailDraft)
async def update_draft(draft_id: str, req: DraftUpdateRequest, user: UserPrincipal = Depends(RoleChecker(["admin", "agent"]))):
    """Inline edit a draft's subject or body."""
    draft = await draft_repository.get(draft_id)
    if not draft or draft.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    draft.subject = req.subject
    draft.body = req.body
    return await draft_repository.save(draft)

@router.post("/{draft_id}/approve", response_model=EmailDraft)
async def approve_draft(draft_id: str, user: UserPrincipal = Depends(RoleChecker(["admin", "agent"]))):
    """Approve a draft and trigger the sending process."""
    draft = await draft_repository.get(draft_id)
    if not draft or draft.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    if draft.status != DraftStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Draft is not pending approval")
        
    draft.status = DraftStatus.APPROVED
    await draft_repository.save(draft)
    
    # In a real app, this would be a Celery task: send_email.delay(draft.id)
    # For now, we will just simulate the notification provider sending it.
    # Note: We need a recipient. We'll use a dummy one for the mockup.
    recipient = "prospect@example.com" 
    await notification_provider.notify(
        user_id=user.user_id,
        recipient=recipient,
        template="outbound_email",
        data={"subject": draft.subject, "html": draft.body}
    )
    
    draft.status = DraftStatus.SENT
    return await draft_repository.save(draft)

@router.post("/{draft_id}/reject", response_model=EmailDraft)
async def reject_draft(draft_id: str, user: UserPrincipal = Depends(RoleChecker(["admin", "agent"]))):
    """Reject a draft. It will not be sent."""
    draft = await draft_repository.get(draft_id)
    if not draft or draft.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    draft.status = DraftStatus.REJECTED
    return await draft_repository.save(draft)
