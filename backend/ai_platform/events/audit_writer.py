import logging
from .models import MissionEvent
from server.db.client import supabase_client

logger = logging.getLogger(__name__)

async def audit_event_writer(event: MissionEvent):
    """
    Subscribes to the EventBus and writes all events to the database async.
    """
    try:
        data = {
            "version": getattr(event, "version", 1),
            "mission_id": event.mission_id,
            "event_type": event.event_type,
            "payload": event.payload,
            "source": event.source,
            "provider": event.provider,
            "duration_ms": event.duration_ms,
            "status": event.status
        }
        
        # Async write to supabase if using the sync client in thread or if supabase_client supports async
        # Supabase python client is synchronous for DB operations typically, 
        # but since we are running this in an async handler, we should ideally run it in an executor.
        import asyncio
        loop = asyncio.get_running_loop()
        
        def _write():
            supabase_client.table("audit_events").insert(data).execute()
            
        await loop.run_in_executor(None, _write)
        
    except Exception as e:
        logger.error(f"Failed to write audit event to DB: {e}")

def register_audit_writer():
    from .bus import global_event_bus
    global_event_bus.subscribe_all(audit_event_writer)
    logger.info("Registered Async Audit Writer to EventBus")
