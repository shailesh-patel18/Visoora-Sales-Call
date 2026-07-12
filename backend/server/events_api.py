from fastapi import APIRouter, Request, Depends
from sse_starlette.sse import EventSourceResponse
from security.rbac import get_current_user, UserPrincipal
from server.sse_manager import subscribe_to_tenant
import structlog

logger = structlog.get_logger("events_api")

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("/stream")
async def stream_events(request: Request, user: UserPrincipal = Depends(get_current_user)):
    """
    Establishes a persistent SSE connection for the authenticated user's tenant.
    """
    logger.info("sse_connection_requested", user_id=user.user_id, tenant_id=user.tenant_id)
    
    # EventSourceResponse handles the infinite generator correctly
    # and automatically deals with client disconnects.
    return EventSourceResponse(subscribe_to_tenant(user.tenant_id))
