import asyncio
from typing import Dict, List
import structlog
from v2.foundation.events.bus import IEventBus, BaseDomainEvent, EventHandler

logger = structlog.get_logger("memory_event_bus")

class MemoryEventBus(IEventBus):
    """
    In-memory adapter for the Event Bus.
    Useful for local development and testing without a Redis dependency.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler):
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)
        logger.info("event_subscribed", event=event_name, handler=handler.__name__)

    async def publish(self, event: BaseDomainEvent):
        handlers = self._subscribers.get(event.event_name, [])
        logger.info("event_published", event=event.event_name, trace_id=event.trace_id, handler_count=len(handlers))
        
        # Dispatch to all handlers asynchronously
        tasks = [handler(event) for handler in handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Global instance for DI
event_bus = MemoryEventBus()
