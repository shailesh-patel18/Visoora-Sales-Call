from fastapi import APIRouter, HTTPException, Depends
from security.config import settings

import uuid
import datetime
import structlog

logger = structlog.get_logger("visoora_dev_tools")
router = APIRouter()

# Add a simple dependency to ensure this is only accessible in Dev/Debug mode
def require_dev_mode():
    if not settings.dev_mode:
        raise HTTPException(status_code=403, detail="Developer tools are disabled.")

@router.post("/dev/seed", dependencies=[Depends(require_dev_mode)])
async def seed_data(profile: str = "default"):
    """
    Instantly injects structured seed data to bypass the onboarding flow.
    Supports different profiles e.g., 'default', 'stripe', 'shopify', 'hubspot'.
    """
    try:
        from supabase import create_client
        import os
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY"))
        if not url or not key:
            raise HTTPException(status_code=500, detail="Missing DB credentials")
        supabase = create_client(url, key)
        
        # 1. Tenant Creation or Retrieval
        res = supabase.table("business_brains").select("tenant_id").limit(1).execute()
        
        if not res.data:
            tenant_id = str(uuid.uuid4())
        else:
            tenant_id = res.data[0]["tenant_id"]

        logger.info("seed_data_started", tenant_id=tenant_id, profile=profile)

        # Base Data
        domain = "acme.com"
        industry = "Healthcare Software"
        icps = ["Hospitals", "Clinics"]

        # Handle different seed profiles
        if profile.lower() == "stripe":
            domain = "stripe.com"
            industry = "Fintech"
            icps = ["E-commerce", "SaaS Startups"]
        elif profile.lower() == "shopify":
            domain = "shopify.com"
            industry = "E-commerce"
            icps = ["Retailers", "DTC Brands"]
            
        # 2. Create a mock Business Brain
        brain_id = str(uuid.uuid4())
        supabase.table("business_brains").insert({
            "id": brain_id,
            "tenant_id": tenant_id,
            "domain": domain,
            "industry": industry,
            "icp": icps,
            "ttl_expires_at": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat()
        }).execute()
        
        # 3. Create a mock Mission
        mission_id = str(uuid.uuid4())
        supabase.table("missions").insert({
            "id": mission_id,
            "tenant_id": tenant_id,
            "business_brain_id": brain_id,
            "mission_type": "Outbound Campaign",
            "goal": f"Find 5 {icps[0]} and draft outreach emails.",
            "status": "running",
            "created_at": datetime.datetime.utcnow().isoformat()
        }).execute()
        
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
            "metadata": {"sources": ["Mock"], "count": 2},
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
        
        return {"status": "success", "tenant_id": tenant_id, "mission_id": mission_id, "brain_id": brain_id, "profile": profile}

    except Exception as e:
        logger.error("seed_data_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
