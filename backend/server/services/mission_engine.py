import uuid
import datetime
import structlog
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from server.storage_manager import supabase_client

logger = structlog.get_logger("mission_engine")

# ----------------------------------------------------
# Mission Execution Engine (DAG Orchestrator)
# ----------------------------------------------------

class MissionTask(BaseModel):
    id: str
    mission_id: str
    agent_type: str
    status: str = "pending" # pending, running, waiting_approval, success, failed
    dependencies: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    result_artifact_id: Optional[str] = None

class Mission(BaseModel):
    id: str
    tenant_id: str
    business_brain_id: str
    mission_type: str
    goal: str
    status: str = "planning"
    progress: List[Dict[str, Any]] = Field(default_factory=list)

def create_mission(tenant_id: str, business_brain_id: str, mission_type: str, goal: str) -> Mission:
    """Creates a new Mission to orchestrate a high-level objective."""
    mission_id = str(uuid.uuid4())
    data = {
        "id": mission_id,
        "tenant_id": tenant_id,
        "business_brain_id": business_brain_id,
        "mission_type": mission_type,
        "goal": goal,
        "status": "planning",
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    if supabase_client:
        supabase_client.table("missions").insert(data).execute()
        
    return Mission(**data)

def emit_mission_event(mission_id: str, event_type: str, task_id: str = None, details: Dict = None):
    """
    Logs an event to the mission timeline and dispatches it to the real-time UI.
    """
    if not supabase_client:
        return
        
    try:
        # Fetch tenant_id for the mission to route the WebSocket message
        res = supabase_client.table("missions").select("tenant_id").eq("id", mission_id).execute()
        tenant_id = res.data[0]["tenant_id"] if res.data else "default_shared_tenant"
        
        event_data = {
            "mission_id": mission_id,
            "task_id": task_id,
            "event_type": event_type,
            "details": details or {},
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        supabase_client.table("mission_events").insert(event_data).execute()
        
        # Fire and forget WS dispatch to not block the synchronous call, 
        # or use asyncio if in an async context. Since this is often called synchronously:
        from server.ws_mission_router import dispatch_mission_event_to_ui
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(dispatch_mission_event_to_ui(tenant_id, event_data))
        except RuntimeError:
            pass # Not in an async loop
            
    except Exception as e:
        logger.error("emit_mission_event_failed", error=str(e))

def add_mission_task(mission_id: str, agent_type: str, dependencies: List[str], payload: Dict[str, Any]) -> MissionTask:
    """Adds a task node to the DAG for this mission."""
    task_id = str(uuid.uuid4())
    data = {
        "id": task_id,
        "mission_id": mission_id,
        "agent_type": agent_type,
        "status": "pending",
        "dependencies": dependencies,
        "payload": payload,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    if supabase_client:
        supabase_client.table("mission_tasks").insert(data).execute()
        
    return MissionTask(**data)

def check_task_dependencies(task: MissionTask) -> bool:
    """Checks if all dependencies for a task have completed successfully."""
    if not task.dependencies:
        return True
        
    if not supabase_client:
        return False
        
    # Fetch status of all dependency tasks
    res = supabase_client.table("mission_tasks").select("id, status").in_("id", task.dependencies).execute()
    if not res.data:
        return False
        
    for parent in res.data:
        if parent.get("status") != "success":
            return False
            
    return True



def spawn_ready_tasks():
    """
    Called periodically (e.g., by worker.py).
    Finds pending tasks where all dependencies are successful, and marks them as ready/running.
    """
    if not supabase_client:
        return
        
    res = supabase_client.table("mission_tasks").select("*, missions!inner(tenant_id)").eq("status", "pending").execute()
    for task_data in res.data:
        task = MissionTask(**task_data)
        if check_task_dependencies(task):
            supabase_client.table("mission_tasks").update({"status": "ready"}).eq("id", task.id).execute()
            
            tenant_id = task_data.get("missions", {}).get("tenant_id")
            if tenant_id:
                job_data = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "workflow_type": task.agent_type,
                    "status": "queued",
                    "payload": {"task_id": task.id, **task.payload},
                    "created_at": datetime.datetime.utcnow().isoformat(),
                    "updated_at": datetime.datetime.utcnow().isoformat()
                }
                supabase_client.table("workflow_jobs").insert(job_data).execute()
                
            logger.info("task_ready_for_execution", task_id=task.id, agent_type=task.agent_type)
            emit_mission_event(task.mission_id, "task_ready", task.id, {"agent_type": task.agent_type})
