import os
import uuid
import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Missing Supabase credentials!")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def seed():
    # Find a tenant from existing data (e.g. business_brains)
    res = supabase.table("business_brains").select("tenant_id").limit(1).execute()
    
    if not res.data:
        # If no tenant exists, just use a dummy one (though the UI might not see it if RLS is strict)
        tenant_id = "00000000-0000-0000-0000-000000000000"
    else:
        tenant_id = res.data[0]["tenant_id"]
        
    print(f"Using tenant_id: {tenant_id}")
    
    # 1. Create a mock Business Brain (if none exists)
    brain_id = str(uuid.uuid4())
    supabase.table("business_brains").insert({
        "id": brain_id,
        "tenant_id": tenant_id,
        "domain": "acme.com",
        "industry": "Healthcare Software",
        "icp": ["Hospitals", "Clinics"],
        "ttl_expires_at": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat()
    }).execute()
    
    # 2. Create a mock Mission
    mission_id = str(uuid.uuid4())
    supabase.table("missions").insert({
        "id": mission_id,
        "tenant_id": tenant_id,
        "business_brain_id": brain_id,
        "mission_type": "Outbound Campaign",
        "goal": "Find 5 Healthcare Clinics in Austin and draft outreach emails.",
        "status": "running",
        "created_at": datetime.datetime.utcnow().isoformat()
    }).execute()
    
    # 3. Create mock Tasks & Artifacts (Inbox items waiting for approval)
    
    # Prospect List Artifact & Task
    artifact1_id = str(uuid.uuid4())
    supabase.table("mission_artifacts").insert({
        "id": artifact1_id,
        "tenant_id": tenant_id,
        "mission_id": mission_id,
        "type": "prospect_list",
        "status": "WAITING_APPROVAL",
        "content": {
            "leads": [
                {"name": "Dr. Smith", "company": "Austin General", "title": "Chief Medical Officer"},
                {"name": "Sarah Connor", "company": "Texas Care", "title": "VP of Operations"}
            ]
        },
        "metadata": {"sources": ["Apollo", "LinkedIn"], "count": 2},
        "created_at": datetime.datetime.utcnow().isoformat()
    }).execute()
    
    supabase.table("mission_tasks").insert({
        "id": str(uuid.uuid4()),
        "mission_id": mission_id,
        "agent_type": "prospecting_agent",
        "status": "waiting_approval",
        "result_artifact_id": artifact1_id,
        "payload": {},
        "created_at": datetime.datetime.utcnow().isoformat()
    }).execute()
    
    # Email Draft Artifact & Task
    artifact2_id = str(uuid.uuid4())
    supabase.table("mission_artifacts").insert({
        "id": artifact2_id,
        "tenant_id": tenant_id,
        "mission_id": mission_id,
        "type": "email_draft",
        "status": "WAITING_APPROVAL",
        "content": {
            "subject": "Streamline Your Clinic's Workflow",
            "body": "Hi Dr. Smith,\n\nI noticed Austin General has been expanding rapidly. Our software helps clinics like yours reduce administrative overhead by 30%.\n\nWould you be open to a quick 10-minute chat next Tuesday?\n\nBest,\nVisoora AI"
        },
        "metadata": {"tokens": 85, "cost": 0.01, "model": "Claude 3.5 Sonnet"},
        "created_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()
    }).execute()
    
    supabase.table("mission_tasks").insert({
        "id": str(uuid.uuid4()),
        "mission_id": mission_id,
        "agent_type": "email_agent",
        "status": "waiting_approval",
        "result_artifact_id": artifact2_id,
        "payload": {"prospect_name": "Dr. Smith"},
        "created_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()
    }).execute()
    
    # Voice Script Artifact & Task
    artifact3_id = str(uuid.uuid4())
    supabase.table("mission_artifacts").insert({
        "id": artifact3_id,
        "tenant_id": tenant_id,
        "mission_id": mission_id,
        "type": "voice_script",
        "status": "WAITING_APPROVAL",
        "content": {
            "objectives": ["Identify pain points", "Book demo"],
            "opening": "Hi Dr. Smith, this is Alex from Visoora. I saw Austin General's recent expansion...",
            "discovery_questions": ["How are you currently handling inbound patient leads?", "Are you struggling with no-shows?"],
            "pain_hypotheses": ["High administrative burden"],
            "objection_library": ["We don't have budget", "We already use Epic"],
            "meeting_goal": "Schedule 15 min discovery call"
        },
        "metadata": {"model": "Deterministic", "estimated_duration": "3 mins"},
        "created_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).isoformat()
    }).execute()
    
    supabase.table("mission_tasks").insert({
        "id": str(uuid.uuid4()),
        "mission_id": mission_id,
        "agent_type": "voice_agent",
        "status": "waiting_approval",
        "result_artifact_id": artifact3_id,
        "payload": {"prospect_name": "Dr. Smith", "phone": "+15551234567"},
        "created_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).isoformat()
    }).execute()
    
    # 4. Create Mission Events for the Dashboard Timeline
    events = [
        {"agent": "Planning Agent", "action": "Analyzing Business Brain and generating execution graph", "type": "info"},
        {"agent": "Prospecting Agent", "action": "Found 12 matching clinics in Austin area", "type": "success"},
        {"agent": "Research Agent", "action": "Deep diving into Austin General's recent expansion news", "type": "info"},
        {"agent": "Email Agent", "action": "Drafted hyper-personalized email for Dr. Smith", "status": "Waiting Approval", "type": "warning"},
        {"agent": "Voice Agent", "action": "Generated tailored conversational script for Dr. Smith", "status": "Waiting Approval", "type": "warning"}
    ]
    
    for i, ev in enumerate(events):
        supabase.table("mission_events").insert({
            "id": str(uuid.uuid4()),
            "mission_id": mission_id,
            "task_id": None,
            "event_type": "agent_action",
            "details": ev,
            "created_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=i)).isoformat()
        }).execute()

    print("Successfully seeded mock data!")

if __name__ == "__main__":
    seed()
