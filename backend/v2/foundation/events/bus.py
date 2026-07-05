from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Any, Dict
from pydantic import BaseModel, Field
import datetime
import uuid

# ---------------------------------------------------------
# Domain Events
# ---------------------------------------------------------

class BaseDomainEvent(BaseModel):
    """
    Base class for all events in the system.
    This enforces strict schema validation for the Event Bus.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    event_name: str
    tenant_id: str
    trace_id: str
    payload: Dict[str, Any]

class MissionStartedEvent(BaseDomainEvent):
    event_name: str = "MissionStarted"

class CallCompletedEvent(BaseDomainEvent):
    event_name: str = "CallCompleted"

# Add more strictly-typed domain events as needed...


# ---------------------------------------------------------
# Interface (Port)
# ---------------------------------------------------------

EventHandler = Callable[[BaseDomainEvent], Awaitable[None]]

class IEventBus(ABC):
    """
    Hexagonal Port for the Event Bus. 
    Decouples event publishing from the actual broker (Redis, Kafka, memory).
    """
    
    @abstractmethod
    async def publish(self, event: BaseDomainEvent):
        """Publishes an event to all subscribers."""
        pass
        
    @abstractmethod
    def subscribe(self, event_name: str, handler: EventHandler):
        """Registers a handler for a specific domain event."""
        pass
