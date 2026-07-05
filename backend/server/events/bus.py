from typing import Callable, Dict, List, Any
import logging
import asyncio

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler to {event_type}")

    def publish(self, event_type: str, payload: Any):
        if event_type not in self._subscribers:
            return
        for handler in self._subscribers[event_type]:
            try:
                # If the handler is a coroutine, schedule it to run in the background
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(payload))
                else:
                    handler(payload)
            except Exception as e:
                logger.error(f"Error handling event {event_type}: {e}")

# Global Event Bus instance
bus = EventBus()
