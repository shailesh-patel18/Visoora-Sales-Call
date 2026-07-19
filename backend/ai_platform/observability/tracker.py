import logging
from typing import Dict, Any
from ..events.models import MissionEvent
from ..events.bus import global_event_bus

logger = logging.getLogger(__name__)

class ObservabilityTracker:
    """
    Subscribes to events to track cost, tokens, and duration per mission.
    In a real system, this could aggregate to a Redis cache or update a mission_metrics table.
    """
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}
        
    async def track_event(self, event: MissionEvent):
        mission_id = event.mission_id
        if mission_id not in self.metrics:
            self.metrics[mission_id] = {
                "total_duration_ms": 0.0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "providers_used": set(),
                "event_count": 0
            }
            
        m = self.metrics[mission_id]
        m["event_count"] += 1
        
        if event.duration_ms:
            m["total_duration_ms"] += event.duration_ms
            
        if event.provider:
            m["providers_used"].add(event.provider)
            
        # Example: Extract token usage from payload if an LLM event
        payload_tokens = event.payload.get("tokens", 0)
        payload_cost = event.payload.get("cost", 0.0)
        
        m["total_tokens"] += payload_tokens
        m["total_cost"] += payload_cost
        
        if event.event_type == "MissionCompleted":
            # Just log the final observability metrics
            logger.info(f"Observability Report for {mission_id}: {m}")

tracker = ObservabilityTracker()

def register_tracker():
    global_event_bus.subscribe_all(tracker.track_event)
    logger.info("Registered ObservabilityTracker to EventBus")
