from typing import Dict, Any, Optional
import structlog
from sales_employee.services import history_service, store, require_tenant_id, utc_now

logger = structlog.get_logger("visoora_delivery_tracker")

def track_delivery_event(
    tenant_id: str,
    lead_id: str,
    event_type: str,
    message_id: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Registers delivery events (delivered, bounced, dropped) into outreach logs.
    """
    require_tenant_id(tenant_id)
    
    # Store event log
    store.insert("delivery_events", {
        "tenant_id": tenant_id,
        "lead_id": lead_id,
        "event_type": event_type,
        "message_id": message_id,
        "metadata": metadata
    })
    
    # Update lead timeline status
    return history_service.add(
        tenant_id=tenant_id,
        lead_id=lead_id,
        channel="email",
        direction="outbound",
        status=event_type, # e.g. delivered, bounced
        content_ref=message_id,
        metadata=metadata
    )

def track_open_event(
    tenant_id: str,
    lead_id: str,
    message_id: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Tracks email open events and registers the signal.
    """
    require_tenant_id(tenant_id)
    
    store.insert("open_events", {
        "tenant_id": tenant_id,
        "lead_id": lead_id,
        "message_id": message_id,
        "metadata": metadata
    })
    
    return history_service.add(
        tenant_id=tenant_id,
        lead_id=lead_id,
        channel="email",
        direction="outbound",
        status="opened",
        content_ref=message_id,
        metadata=metadata
    )

def track_reply_event(
    tenant_id: str,
    lead_id: str,
    message_id: str,
    reply_body: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Tracks inbound email replies from prospects.
    """
    require_tenant_id(tenant_id)
    
    store.insert("reply_events", {
        "tenant_id": tenant_id,
        "lead_id": lead_id,
        "message_id": message_id,
        "reply_body": reply_body,
        "metadata": metadata
    })
    
    # Inbound email reply registered on the timeline
    return history_service.add(
        tenant_id=tenant_id,
        lead_id=lead_id,
        channel="email",
        direction="inbound",
        status="replied",
        content_ref=message_id,
        metadata={"reply_body": reply_body, **metadata}
    )
