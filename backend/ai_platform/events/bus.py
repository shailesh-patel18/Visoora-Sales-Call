import asyncio
import logging
from typing import Callable, Awaitable, List, Dict
from .models import MissionEvent

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[MissionEvent], Awaitable[None]]

class EventBus:
    """
    In-memory Pub/Sub event bus.
    Handles routing events to subscribers asynchronously.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []
        self._task_queue = asyncio.Queue()
        self._worker_task = None

    def start(self):
        """Starts the background worker to process events."""
        if not self._worker_task:
            self._worker_task = asyncio.create_task(self._process_events())

    async def stop(self):
        """Stops the background worker gracefully."""
        if self._worker_task:
            await self._task_queue.put(None) # Sentinel to stop
            await self._worker_task
            self._worker_task = None

    def subscribe(self, event_type: str, handler: EventHandler):
        """Subscribe to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler):
        """Subscribe to all events (useful for audit logging)."""
        self._global_subscribers.append(handler)

    def publish(self, event: MissionEvent):
        """
        Publish an event to the bus. Returns immediately.
        The event is processed asynchronously by the worker task.
        """
        try:
            self._task_queue.put_nowait(event)
        except Exception as e:
            logger.error(f"Failed to enqueue event {event.event_type}: {e}")

    async def _process_events(self):
        while True:
            event = await self._task_queue.get()
            if event is None:
                self._task_queue.task_done()
                break
                
            try:
                # Get all handlers for this event
                handlers = self._subscribers.get(event.event_type, [])
                handlers = handlers + self._global_subscribers
                
                # Execute all handlers concurrently
                if handlers:
                    tasks = []
                    for h in handlers:
                        if asyncio.iscoroutinefunction(h):
                            tasks.append(h(event))
                        else:
                            # Run sync handlers in executor or simply wrap them
                            h(event)
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error processing event {event.event_type}: {e}")
            finally:
                self._task_queue.task_done()

# Global singleton
global_event_bus = EventBus()
# The application or tests must call global_event_bus.start() once the event loop is running.
