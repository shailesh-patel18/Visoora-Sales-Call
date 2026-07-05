from fastapi import APIRouter, Request, BackgroundTasks
import structlog
from v2.foundation.events.memory_adapter import event_bus
from v2.foundation.events.bus import BaseDomainEvent

logger = structlog.get_logger("twilio_adapter")

router = APIRouter(prefix="/api/v2/twilio", tags=["Twilio"])

class CallCompletedEvent(BaseDomainEvent):
    event_name: str = "CallCompleted"

@router.post("/webhook")
async def twilio_webhook_interceptor(request: Request, background_tasks: BackgroundTasks):
    """
    Intercepts the incoming Twilio webhook and routes it to the v2 EventBus and VoiceAgent.
    This replaces the legacy `server/twilio_handler.py` while maintaining API contract parity.
    """
    # In reality, this parses the Twilio form data
    # form_data = await request.form()
    # call_sid = form_data.get("CallSid")
    # status = form_data.get("CallStatus")
    
    call_sid = "mock_call_sid_123"
    status = "completed"
    
    logger.info("twilio_webhook_received", call_sid=call_sid, status=status)
    
    if status == "completed":
        # Emit Domain Event for the Learning Engine to pick up
        evt = CallCompletedEvent(
            tenant_id="anonymous", # Would extract from context/DB
            trace_id=call_sid,
            payload={
                "call_sid": call_sid,
                "outcome": "objection_pricing", # Mocking a failed call for the Learning Engine
                "duration": 45
            }
        )
        background_tasks.add_task(event_bus.publish, evt)
        
    return {"status": "success"}
