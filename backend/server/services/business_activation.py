import structlog
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from security.rbac import get_current_user, UserPrincipal
from server.storage_manager import supabase_admin_client as supabase_client

logger = structlog.get_logger("business_activation")

activation_router = APIRouter(prefix="/api/activation", tags=["Business Activation"], dependencies=[Depends(get_current_user)])

class ClaimBrainRequest(BaseModel):
    report_id: str

@activation_router.post("/claim-brain")
async def claim_brain(payload: ClaimBrainRequest, user: UserPrincipal = Depends(get_current_user)):
    """
    Transfers ownership of a public Business Brain (report_id) to the authenticated user's tenant_id.
    Emits a BusinessBrainClaimed event for background processing (CRM population, etc.).
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    report_id = payload.report_id
    
    # 1. Fetch the brain to ensure it exists and belongs to anonymous
    res = supabase_client.table("business_brains").select("tenant_id, metadata").eq("id", report_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Business Brain not found")
        
    brain = res.data[0]
    if brain.get("tenant_id") != "anonymous":
        # Check if it already belongs to this tenant, which is fine (idempotent)
        if brain.get("tenant_id") == user.tenant_id:
            return {"success": True, "message": "Brain already claimed"}
        raise HTTPException(status_code=403, detail="Brain already claimed by another tenant")

    # 2. Update the tenant_id
    update_res = supabase_client.table("business_brains").update({
        "tenant_id": user.tenant_id
    }).eq("id", report_id).execute()
    
    if not update_res.data:
        raise HTTPException(status_code=500, detail="Failed to claim Business Brain")
        
    logger.info("business_brain_claimed", report_id=report_id, new_tenant_id=user.tenant_id)

    # 3. Emit BusinessBrainClaimed event for async provisioning (Sprint 1)
    # We will log it in workflow_events so the background worker can pick it up
    event_payload = {
        "report_id": report_id,
        "tenant_id": user.tenant_id,
        "action": "BusinessBrainClaimed"
    }
    
    supabase_client.table("workflow_events").insert({
        "job_id": report_id, # Reusing report_id as job_id for tracking
        "event_type": "WorkspaceProvisioningStarted",
        "payload": event_payload
    }).execute()

    return {"success": True, "message": "Business Brain claimed successfully"}

@activation_router.get("/brain")
async def get_brain(user: UserPrincipal = Depends(get_current_user)):
    """
    Returns the Business Brain for the current authenticated tenant.
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    res = supabase_client.table("business_brains").select("*").eq("tenant_id", user.tenant_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="No Business Brain found for this tenant")

    # Order by created_at desc if there are multiple, returning the latest
    brains = sorted(res.data, key=lambda x: x.get("created_at", ""), reverse=True)
    return brains[0]
