import uuid
import datetime
import structlog
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from server.storage_manager import supabase_admin_client as supabase_client

logger = structlog.get_logger("workflow_engine")

class WorkflowStep(BaseModel):
    step_id: str
    label: str
    status: str = "pending" # pending, running, success, failed

class WorkflowJob(BaseModel):
    id: str
    workflow_type: str
    tenant_id: str
    user_id: Optional[str] = None
    status: str = "queued"
    payload: Dict[str, Any] = Field(default_factory=dict)
    progress: List[WorkflowStep] = Field(default_factory=list)
    current_step: Optional[str] = None
    result_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str

class WorkflowEvent(BaseModel):
    job_id: str
    event_type: str
    step_name: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

def create_workflow_job(workflow_type: str, tenant_id: str, payload: Dict[str, Any], steps: List[WorkflowStep]) -> WorkflowJob:
    job_id = str(uuid.uuid4())
    job_data = {
        "id": job_id,
        "workflow_type": workflow_type,
        "tenant_id": tenant_id,
        "status": "queued",
        "payload": payload,
        "progress": [s.model_dump() for s in steps],
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    if supabase_client:
        try:
            supabase_client.table("workflow_jobs").insert(job_data).execute()
            logger.info("workflow_job_created", job_id=job_id, workflow_type=workflow_type)
        except Exception as e:
            logger.error("workflow_job_creation_failed", error=str(e))
        
    return WorkflowJob(**job_data)

def emit_workflow_event(job_id: str, event_type: str, step_name: str = None, payload: Dict[str, Any] = None, tenant_id: str = None):
    # Try to fetch tenant_id from context if not provided
    if not tenant_id:
        try:
            from security.logging import tenant_id_var
            tid = tenant_id_var.get()
            if tid and tid != "system":
                tenant_id = tid
        except Exception:
            pass

    # Fallback to DB lookup if we only have job_id
    if not tenant_id and supabase_client:
        try:
            res = supabase_client.table("workflow_jobs").select("tenant_id").eq("id", job_id).execute()
            if res.data:
                tenant_id = res.data[0]["tenant_id"]
        except Exception:
            pass

    event_data = {
        "job_id": job_id,
        "event_type": event_type,
        "step_name": step_name,
        "payload": payload or {}
    }
    if supabase_client:
        try:
            supabase_client.table("workflow_events").insert(event_data).execute()
        except Exception as e:
            logger.error("workflow_event_failed", error=str(e))
            
    # Broadcast via SSE Manager
    if tenant_id:
        try:
            from server.sse_manager import sse_broadcast
            sse_broadcast(tenant_id, event_data)
        except ImportError:
            pass # SSE Manager might not be imported yet

def update_job_status(job_id: str, status: str, result_id: str = None, error: str = None):
    updates = {"status": status, "updated_at": datetime.datetime.utcnow().isoformat()}
    if result_id:
        updates["result_id"] = result_id
    if error:
        updates["error"] = error
        
    if supabase_client:
        try:
            supabase_client.table("workflow_jobs").update(updates).eq("id", job_id).execute()
            logger.info("workflow_job_updated", job_id=job_id, status=status)
        except Exception as e:
            logger.error("workflow_job_update_failed", error=str(e))

def update_job_step(job_id: str, step_id: str, status: str):
    """
    Updates the specific step in the JSONB progress array and emits an event.
    """
    if not supabase_client:
        return
        
    try:
        res = supabase_client.table("workflow_jobs").select("progress").eq("id", job_id).execute()
        if not res.data:
            return
            
        progress = res.data[0].get("progress", [])
        for step in progress:
            if step.get("step_id") == step_id:
                step["status"] = status
                
        supabase_client.table("workflow_jobs").update({
            "progress": progress,
            "current_step": step_id if status == "running" else None,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }).eq("id", job_id).execute()
        
        # Emit the event!
        emit_workflow_event(job_id, event_type=f"step_{status}", step_name=step_id)
        
    except Exception as e:
        logger.error("workflow_step_update_failed", error=str(e))
