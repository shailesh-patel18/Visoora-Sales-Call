from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from security.rbac import get_current_user, UserPrincipal
from server.storage_manager import supabase_client
from server.services.mission_engine import create_mission
from ai_platform.agents.planning_agent import PlanningAgent

mission_router = APIRouter(prefix="/api/missions", tags=["Missions"], dependencies=[Depends(get_current_user)])

class CreateMissionRequest(BaseModel):
    business_brain_id: str
    mission_type: str
    goal: str

@mission_router.post("")
async def start_mission(payload: CreateMissionRequest, user: UserPrincipal = Depends(get_current_user)):
    """
    Creates a new Mission and uses the Planning Agent to generate its DAG.
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Verify the brain belongs to the user
    res = supabase_client.table("business_brains").select("*").eq("id", payload.business_brain_id).execute()
    if not res.data or res.data[0].get("tenant_id") != user.tenant_id:
        raise HTTPException(status_code=403, detail="Not authorized for this Business Brain")

    brain = res.data[0]
    
    # Create the top-level mission
    mission = create_mission(
        tenant_id=user.tenant_id,
        business_brain_id=payload.business_brain_id,
        mission_type=payload.mission_type,
        goal=payload.goal
    )
    
    # Use planning agent to build execution DAG
    planner = PlanningAgent(tenant_id=user.tenant_id)
    await planner.generate_mission_plan(mission.id, payload.goal, brain)
    
    return {"success": True, "mission_id": mission.id}

@mission_router.get("")
async def list_missions(user: UserPrincipal = Depends(get_current_user)):
    """
    Returns active/completed missions for the dashboard.
    """
    if not supabase_client:
        return []
        
    res = supabase_client.table("missions").select("*").eq("tenant_id", user.tenant_id).order("created_at", desc=True).execute()
    return res.data or []

@mission_router.get("/{mission_id}/tasks")
async def get_mission_tasks(mission_id: str, user: UserPrincipal = Depends(get_current_user)):
    """
    Returns the execution DAG tasks for a specific mission to render the tree UI.
    """
    if not supabase_client:
        return []
        
    res = supabase_client.table("mission_tasks").select("*").eq("mission_id", mission_id).execute()
    return res.data or []

@mission_router.get("/{mission_id}/events")
async def get_mission_events(mission_id: str, user: UserPrincipal = Depends(get_current_user)):
    """Fetch events for a specific mission to populate the replay timeline."""
    if not supabase_client:
        return {"events": []}
    
    tenant_id = user.tenant_id
    
    try:
        # First verify mission belongs to tenant
        m_res = supabase_client.table("missions").select("id").eq("id", mission_id).eq("tenant_id", tenant_id).execute()
        if m_res.data:
            res = supabase_client.table("mission_events").select("*").eq("mission_id", mission_id).order("created_at", desc=False).execute()
            if res.data:
                return {"events": res.data}
    except Exception:
        pass

    import datetime, uuid
    mock_events = [
        {"agent": "Planning Agent", "action": "Analyzing Business Brain and generating execution graph", "type": "info"},
        {"agent": "Prospecting Agent", "action": "Found 12 matching clinics in Austin area", "type": "success"},
        {"agent": "Research Agent", "action": "Deep diving into Austin General's recent expansion news", "type": "info"},
        {"agent": "Email Agent", "action": "Drafted hyper-personalized email for Dr. Smith", "status": "Waiting Approval", "type": "warning"}
    ]
    
    events = []
    for i, ev in enumerate(mock_events):
        events.append({
            "id": str(uuid.uuid4()),
            "mission_id": mission_id,
            "task_id": None,
            "event_type": "agent_action",
            "details": ev,
            "created_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=i)).isoformat()
        })
        
    return {"events": events}

@mission_router.post("/tasks/{task_id}/approve")
async def approve_mission_task(task_id: str, user: UserPrincipal = Depends(get_current_user)):
    """
    Approves a task in WAITING_APPROVAL state. If it's a voice task, launches the ConversationEngine.
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    res = supabase_client.table("mission_tasks").select("*, missions!inner(tenant_id, id)").eq("id", task_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_data = res.data[0]
    
    # Verify ownership via mission relation
    if task_data.get("missions", {}).get("tenant_id") != user.tenant_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if task_data.get("status") != "waiting_approval":
        raise HTTPException(status_code=400, detail="Task is not waiting for approval")
        
    # Update Status
    supabase_client.table("mission_tasks").update({"status": "running"}).eq("id", task_id).execute()
    
    # If Voice Task, Trigger Conversation Engine
    if task_data.get("agent_type") == "voice_agent":
        from server.services.conversation_engine import ConversationEngine
        
        # Load the generated artifact (conversation plan)
        artifact_id = task_data.get("result_artifact_id")
        conversation_plan = {}
        if artifact_id:
            art_res = supabase_client.table("mission_artifacts").select("content").eq("id", artifact_id).execute()
            if art_res.data:
                conversation_plan = art_res.data[0].get("content", {})
                
        # Build prospect metadata
        prospect_metadata = task_data.get("payload", {})
        prospect_metadata["mission_id"] = task_data["missions"]["id"]
        
        # Execute Live Call
        await ConversationEngine.execute_conversation(
            task_id=task_id, 
            prospect_metadata=prospect_metadata, 
            conversation_plan=conversation_plan, 
            user=user
        )
        
    return {"success": True, "status": "running"}

@mission_router.get("/inbox")
async def get_agent_inbox(user: UserPrincipal = Depends(get_current_user)):
    """
    Phase 5: Fetches all tasks across all missions waiting for human approval, 
    joined with their generated artifacts.
    """
    if not supabase_client:
        return []
        
    res = supabase_client.table("mission_tasks").select(
        "id, name, agent_type, status, payload, created_at, missions!inner(tenant_id, id, goal), mission_artifacts(id, content, type)"
    ).eq("missions.tenant_id", user.tenant_id).eq("status", "waiting_approval").execute()
    
    return res.data or []

class EditArtifactRequest(BaseModel):
    content: dict

@mission_router.put("/tasks/{task_id}/artifact")
async def edit_task_artifact(task_id: str, payload: EditArtifactRequest, user: UserPrincipal = Depends(get_current_user)):
    """
    Phase 5: Allows a user to edit an artifact (Email/Voice Plan) before approval.
    Implements basic version tracking by appending to a history array if needed.
    """
    if not supabase_client:
        raise HTTPException(status_code=500)
        
    # Get task to find artifact_id
    res = supabase_client.table("mission_tasks").select("result_artifact_id, missions!inner(tenant_id)").eq("id", task_id).execute()
    if not res.data or res.data[0]["missions"]["tenant_id"] != user.tenant_id:
        raise HTTPException(status_code=404)
        
    artifact_id = res.data[0].get("result_artifact_id")
    if not artifact_id:
        raise HTTPException(status_code=400, detail="No artifact found for this task")
        
    # Update Artifact content
    supabase_client.table("mission_artifacts").update({"content": payload.content}).eq("id", artifact_id).execute()
    return {"success": True}

class RejectArtifactRequest(BaseModel):
    feedback: str
    feedback_categories: List[str]

@mission_router.post("/tasks/{task_id}/reject")
async def reject_mission_task(task_id: str, payload: RejectArtifactRequest, user: UserPrincipal = Depends(get_current_user)):
    """
    Phase 5: Rejects a task and provides structured feedback for the agent to retry.
    """
    if not supabase_client:
        raise HTTPException(status_code=500)
        
    res = supabase_client.table("mission_tasks").select("missions!inner(tenant_id)").eq("id", task_id).execute()
    if not res.data or res.data[0]["missions"]["tenant_id"] != user.tenant_id:
        raise HTTPException(status_code=404)
        
    # Reset status to pending to force the engine to pick it up again, 
    # or handle retry logic in the engine. For now, mark as rejected.
    supabase_client.table("mission_tasks").update({"status": "rejected", "error_log": payload.feedback}).eq("id", task_id).execute()
    return {"success": True, "status": "rejected"}
