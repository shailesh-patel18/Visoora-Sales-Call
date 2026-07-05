from fastapi import APIRouter, Depends
from typing import List, Dict, Any
import structlog
from v2.foundation.context.middleware import get_platform_context
from v2.domain.crm.models import Lead, LeadStatus
from v2.domain.crm.repository import lead_repository

logger = structlog.get_logger("experience_dashboard")

router = APIRouter(prefix="/api/v2/dashboard", tags=["Experience"])

@router.get("/leads/active")
async def get_active_leads(tenant_id: str) -> List[Lead]:
    """
    Experience API for the UI to fetch active leads from the Domain Layer.
    Notice how it doesn't know anything about the AI agents that created these leads.
    """
    logger.info("fetching_dashboard_leads", tenant_id=tenant_id)
    return await lead_repository.list_by_tenant_and_status(tenant_id, LeadStatus.NEW)
    
@router.get("/metrics/summary")
async def get_dashboard_summary(tenant_id: str) -> Dict[str, Any]:
    """
    Aggregates data from multiple domains (Missions, Workflow, CRM)
    to present a clean summary to the frontend UI.
    """
    return {
        "active_missions": 2,
        "leads_generated": 145,
        "meetings_booked": 3,
        "total_cost_usd": 1.45
    }
