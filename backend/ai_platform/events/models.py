import time
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

def current_iso_time() -> str:
    return datetime.utcnow().isoformat() + "Z"

class MissionEvent(BaseModel):
    """
    Base class for all mission events.
    """
    version: int = 1
    mission_id: str
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    source: str = "system"
    provider: Optional[str] = None
    duration_ms: Optional[float] = None
    status: Optional[str] = None
    timestamp: str = Field(default_factory=current_iso_time)

# Examples of specific event types we might emit

class MissionStarted(MissionEvent):
    def __init__(self, mission_id: str, **kwargs):
        super().__init__(mission_id=mission_id, event_type="MissionStarted", **kwargs)

class NodeStarted(MissionEvent):
    def __init__(self, mission_id: str, node_name: str, **kwargs):
        super().__init__(
            mission_id=mission_id, 
            event_type="NodeStarted", 
            payload={"node": node_name, **kwargs.get("payload", {})},
            **{k:v for k,v in kwargs.items() if k != "payload"}
        )

class NodeCompleted(MissionEvent):
    def __init__(self, mission_id: str, node_name: str, duration_ms: float, result: Any, **kwargs):
        super().__init__(
            mission_id=mission_id, 
            event_type="NodeCompleted", 
            payload={"node": node_name, "result": result, **kwargs.get("payload", {})},
            duration_ms=duration_ms,
            status="success",
            **{k:v for k,v in kwargs.items() if k != "payload"}
        )

class NodeFailed(MissionEvent):
    def __init__(self, mission_id: str, node_name: str, error: str, **kwargs):
        super().__init__(
            mission_id=mission_id, 
            event_type="NodeFailed", 
            payload={"node": node_name, "error": error, **kwargs.get("payload", {})},
            status="failed",
            **{k:v for k,v in kwargs.items() if k != "payload"}
        )

class MissionCompleted(MissionEvent):
    def __init__(self, mission_id: str, final_state: Dict[str, Any], **kwargs):
        super().__init__(
            mission_id=mission_id, 
            event_type="MissionCompleted", 
            payload={"final_state": final_state, **kwargs.get("payload", {})},
            status="success",
            **{k:v for k,v in kwargs.items() if k != "payload"}
        )

class MissionEvaluated(MissionEvent):
    def __init__(self, mission_id: str, scores: Dict[str, Any], **kwargs):
        super().__init__(
            mission_id=mission_id, 
            event_type="MissionEvaluated", 
            payload={"scores": scores, **kwargs.get("payload", {})},
            status="success",
            **{k:v for k,v in kwargs.items() if k != "payload"}
        )

class MissionPaused(MissionEvent):
    def __init__(self, mission_id: str, **kwargs):
        super().__init__(mission_id=mission_id, event_type="MissionPaused", **kwargs)

class ApprovalRequested(MissionEvent):
    def __init__(self, mission_id: str, policy: str, payload: Dict[str, Any] = None, **kwargs):
        super().__init__(mission_id=mission_id, event_type="ApprovalRequested", payload={"policy": policy, **(payload or {})}, **kwargs)

class ApprovalGranted(MissionEvent):
    def __init__(self, mission_id: str, **kwargs):
        super().__init__(mission_id=mission_id, event_type="ApprovalGranted", **kwargs)

class ApprovalRejected(MissionEvent):
    def __init__(self, mission_id: str, **kwargs):
        super().__init__(mission_id=mission_id, event_type="ApprovalRejected", **kwargs)

class MissionResumed(MissionEvent):
    def __init__(self, mission_id: str, **kwargs):
        super().__init__(mission_id=mission_id, event_type="MissionResumed", **kwargs)

