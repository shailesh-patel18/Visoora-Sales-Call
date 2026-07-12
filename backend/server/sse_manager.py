import asyncio
import json
import structlog
from typing import Dict, Any

logger = structlog.get_logger("sse_manager")

# In-memory pub-sub for SSE events. 
# Maps tenant_id -> list of asyncio.Queue
# In a multi-worker production setup (like multiple uvicorn workers or serverless), 
# this would be replaced with Redis Pub/Sub.
_SUBSCRIBERS: Dict[str, list[asyncio.Queue]] = {}

def sse_broadcast(tenant_id: str, event_data: Dict[str, Any]):
    """Broadcasts an event to all subscribers of a specific tenant_id."""
    if tenant_id not in _SUBSCRIBERS:
        return
        
    payload_str = json.dumps(event_data)
    
    for q in _SUBSCRIBERS[tenant_id]:
        try:
            q.put_nowait(payload_str)
        except asyncio.QueueFull:
            pass

async def subscribe_to_tenant(tenant_id: str):
    """
    Generator for Server-Sent Events (SSE) that yields properly formatted SSE strings.
    """
    if tenant_id not in _SUBSCRIBERS:
        _SUBSCRIBERS[tenant_id] = []
        
    q = asyncio.Queue(maxsize=100)
    _SUBSCRIBERS[tenant_id].append(q)
    
    logger.info("sse_client_connected", tenant_id=tenant_id, active_clients=len(_SUBSCRIBERS[tenant_id]))
    
    try:
        # Initial connection ping
        yield f"data: {json.dumps({'event_type': 'connected', 'tenant_id': tenant_id})}\n\n"
        
        while True:
            # Wait for next event broadcast by the background worker
            message = await q.get()
            yield f"data: {message}\n\n"
            
    except asyncio.CancelledError:
        logger.info("sse_client_disconnected", tenant_id=tenant_id)
        
    finally:
        if tenant_id in _SUBSCRIBERS:
            _SUBSCRIBERS[tenant_id].remove(q)
            if not _SUBSCRIBERS[tenant_id]:
                del _SUBSCRIBERS[tenant_id]
