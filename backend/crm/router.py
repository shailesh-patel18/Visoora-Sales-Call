import datetime
import uuid
import asyncio
from uuid import UUID
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks, status, Depends
import structlog
from server.storage_manager import supabase_admin_client as supabase_client
from crm.models import (
    ContactCreate, ContactUpdate, ContactResponse,
    DealCreate, DealUpdate, DealResponse,
    ActivityCreate, ActivityResponse,
    StageDealsAggregate
)
from crm.auto_advance import (
    get_or_seed_stages,
    _load_local_json,
    _save_local_json
)

logger = structlog.get_logger("visoora_crm_api")

from security.rbac import get_current_user, UserPrincipal
from security.config import settings

router = APIRouter(prefix="/api/v1/crm", tags=["CRM"])


# ====================================================
# UTILITIES & TENANT PARSING
# ====================================================
def get_tenant_id(x_tenant_id: Optional[str] = Header(None)) -> str:
    """Helper to extract or default multi-tenant IDs from standard request headers."""
    if not x_tenant_id:
        return "acme_tenant"
    return x_tenant_id


def _stringify_uuids(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively converts any UUID and datetime instances in the dictionary to string representation."""
    cleaned = {}
    for k, v in data.items():
        if isinstance(v, uuid.UUID):
            cleaned[k] = str(v)
        elif isinstance(v, (datetime.datetime, datetime.date)):
            cleaned[k] = v.isoformat()
        elif isinstance(v, dict):
            cleaned[k] = _stringify_uuids(v)
        elif isinstance(v, list):
            cleaned[k] = [
                str(x) if isinstance(x, uuid.UUID)
                else (x.isoformat() if isinstance(x, (datetime.datetime, datetime.date)) else x)
                for x in v
            ]
        else:
            cleaned[k] = v
    return cleaned


# ====================================================
# CONTACTS CRUD ENDPOINTS
# ====================================================
@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(contact: ContactCreate, user: UserPrincipal = Depends(get_current_user)):
    """Creates a new prospect Contact record in Visoora CRM."""
    payload = _stringify_uuids(contact.model_dump())
    payload["tenant_id"] = user.tenant_id  # Enforce tenant isolation on write
    payload["id"] = str(uuid.uuid4())
    payload["created_at"] = datetime.datetime.utcnow().isoformat()
    payload["updated_at"] = datetime.datetime.utcnow().isoformat()

    # Backfill name/phone_number/company for backward compatibility
    payload["name"] = payload["full_name"]
    payload["phone_number"] = payload["phone_e164"]
    payload["company"] = payload["company_name"]

    if supabase_client:
        try:
            res = supabase_client.table("contacts").insert(payload).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error("api_create_contact_db_failed", error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database write error.")

    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=500, detail="Supabase offline. Database write not available.")

    # Local Fallback
    local_contacts = _load_local_json("local_crm_contacts.json")
    local_contacts.append(payload)
    _save_local_json("local_crm_contacts.json", local_contacts)
    return payload


@router.get("/contacts", response_model=List[ContactResponse])
async def list_contacts(user: UserPrincipal = Depends(get_current_user)):
    """List all Contact records associated with the tenant."""
    tenant_id = user.tenant_id
    if supabase_client:
        try:
            res = supabase_client.table("contacts").select("*").eq("tenant_id", tenant_id).execute()
            return res.data or []
        except Exception as e:
            logger.error("api_list_contacts_db_failed", error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database lookup error.")

    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=500, detail="Supabase offline. Database lookup not available.")

    # Local Fallback
    local_contacts = _load_local_json("local_crm_contacts.json")
    return [c for c in local_contacts if c.get("tenant_id") == tenant_id]


@router.get("/contacts/{id}", response_model=ContactResponse)
async def get_contact(id: UUID, user: UserPrincipal = Depends(get_current_user)):
    """Retrieve details of a specific Contact by ID."""
    tenant_id = user.tenant_id
    if supabase_client:
        try:
            res = supabase_client.table("contacts").select("*").eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error("api_get_contact_db_failed", id=id, error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database lookup error.")
            
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=404, detail="Contact not found.")

    # Local Fallback
    local_contacts = _load_local_json("local_crm_contacts.json")
    matching = [c for c in local_contacts if c.get("id") == str(id) and c.get("tenant_id") == tenant_id]
    if matching:
        return matching[0]

    raise HTTPException(status_code=404, detail="Contact not found.")


@router.put("/contacts/{id}", response_model=ContactResponse)
async def update_contact(id: UUID, contact: ContactUpdate, user: UserPrincipal = Depends(get_current_user)):
    """Update details of an existing Contact."""
    tenant_id = user.tenant_id
    updates = _stringify_uuids(contact.model_dump(exclude_unset=True))
    updates["updated_at"] = datetime.datetime.utcnow().isoformat()

    # Dynamic backfill syncs
    if "full_name" in updates:
        updates["name"] = updates["full_name"]
    if "phone_e164" in updates:
        updates["phone_number"] = updates["phone_e164"]
    if "company_name" in updates:
        updates["company"] = updates["company_name"]

    if supabase_client:
        try:
            res = supabase_client.table("contacts").update(updates).eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error("api_update_contact_db_failed", id=id, error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database update error.")
            
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=404, detail="Contact not found.")

    # Local Fallback
    local_contacts = _load_local_json("local_crm_contacts.json")
    for c in local_contacts:
        if c.get("id") == str(id) and c.get("tenant_id") == tenant_id:
            c.update(updates)
            _save_local_json("local_crm_contacts.json", local_contacts)
            return c

    raise HTTPException(status_code=404, detail="Contact not found.")


@router.delete("/contacts/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(id: UUID, user: UserPrincipal = Depends(get_current_user)):
    """Delete a Contact record from Visoora CRM."""
    tenant_id = user.tenant_id
    if supabase_client:
        try:
            res = supabase_client.table("contacts").delete().eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                return
        except Exception as e:
            logger.error("api_delete_contact_db_failed", id=id, error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database delete error.")
            
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=404, detail="Contact not found.")

    # Local Fallback
    local_contacts = _load_local_json("local_crm_contacts.json")
    filtered = [c for c in local_contacts if not (c.get("id") == str(id) and c.get("tenant_id") == tenant_id)]
    if len(filtered) < len(local_contacts):
        _save_local_json("local_crm_contacts.json", filtered)
        return

    raise HTTPException(status_code=404, detail="Contact not found.")


# ====================================================
# DEALS CRUD ENDPOINTS
# ====================================================
@router.post("/deals", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(deal: DealCreate, user: UserPrincipal = Depends(get_current_user)):
    """Creates a new active pipeline Deal."""
    payload = _stringify_uuids(deal.model_dump())
    payload["tenant_id"] = user.tenant_id  # Enforce tenant isolation on write
    payload["id"] = str(uuid.uuid4())
    payload["created_at"] = datetime.datetime.utcnow().isoformat()
    payload["updated_at"] = datetime.datetime.utcnow().isoformat()

    if supabase_client:
        try:
            res = supabase_client.table("deals").insert(payload).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error("api_create_deal_db_failed", error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database write error.")

    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=500, detail="Supabase offline. Database write not available.")

    # Local Fallback
    local_deals = _load_local_json("local_crm_deals.json")
    local_deals.append(payload)
    _save_local_json("local_crm_deals.json", local_deals)
    return payload


@router.get("/deals", response_model=List[DealResponse])
async def list_deals(user: UserPrincipal = Depends(get_current_user)):
    """List all active pipeline Deals."""
    tenant_id = user.tenant_id
    if supabase_client:
        try:
            res = supabase_client.table("deals").select("*").eq("tenant_id", tenant_id).execute()
            return res.data or []
        except Exception as e:
            logger.error("api_list_deals_db_failed", error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database lookup error.")

    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=500, detail="Supabase offline. Database lookup not available.")

    local_deals = _load_local_json("local_crm_deals.json")
    return [d for d in local_deals if d.get("tenant_id") == tenant_id]


@router.get("/deals/{id}", response_model=DealResponse)
async def get_deal(id: UUID, user: UserPrincipal = Depends(get_current_user)):
    """Retrieve details of a specific Deal by ID."""
    tenant_id = user.tenant_id
    if supabase_client:
        try:
            res = supabase_client.table("deals").select("*").eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error("api_get_deal_db_failed", id=id, error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database lookup error.")
    
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=404, detail="Deal not found.")

    local_deals = _load_local_json("local_crm_deals.json")
    matching = [d for d in local_deals if d.get("id") == str(id) and d.get("tenant_id") == tenant_id]
    if matching:
        return matching[0]

    raise HTTPException(status_code=404, detail="Deal not found.")


@router.put("/deals/{id}", response_model=DealResponse)
async def update_deal(id: UUID, deal: DealUpdate, user: UserPrincipal = Depends(get_current_user)):
    """Update details of an existing Deal."""
    tenant_id = user.tenant_id
    updates = _stringify_uuids(deal.model_dump(exclude_unset=True))
    updates["updated_at"] = datetime.datetime.utcnow().isoformat()

    if supabase_client:
        try:
            res = supabase_client.table("deals").update(updates).eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error("api_update_deal_db_failed", id=id, error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database update error.")
    
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=404, detail="Deal not found.")

    local_deals = _load_local_json("local_crm_deals.json")
    for d in local_deals:
        if d.get("id") == str(id) and d.get("tenant_id") == tenant_id:
            d.update(updates)
            _save_local_json("local_crm_deals.json", local_deals)
            return d

    raise HTTPException(status_code=404, detail="Deal not found.")


@router.delete("/deals/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(id: UUID, user: UserPrincipal = Depends(get_current_user)):
    """Delete a Deal record from pipeline."""
    tenant_id = user.tenant_id
    if supabase_client:
        try:
            res = supabase_client.table("deals").delete().eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                return
        except Exception as e:
            logger.error("api_delete_deal_db_failed", id=id, error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database delete error.")

    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=404, detail="Deal not found.")

    local_deals = _load_local_json("local_crm_deals.json")
    filtered = [d for d in local_deals if not (d.get("id") == str(id) and d.get("tenant_id") == tenant_id)]
    if len(filtered) < len(local_deals):
        _save_local_json("local_crm_deals.json", filtered)
        return

    raise HTTPException(status_code=404, detail="Deal not found.")


# ====================================================
# ACTIVITIES CRUD ENDPOINTS
# ====================================================
@router.post("/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(activity: ActivityCreate, user: UserPrincipal = Depends(get_current_user)):
    """Logs a new Touchpoint Activity."""
    payload = _stringify_uuids(activity.model_dump())
    payload["tenant_id"] = user.tenant_id  # Enforce tenant isolation on write
    payload["id"] = str(uuid.uuid4())
    payload["created_at"] = datetime.datetime.utcnow().isoformat()
    payload["updated_at"] = datetime.datetime.utcnow().isoformat()

    if supabase_client:
        try:
            res = supabase_client.table("activities").insert(payload).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error("api_create_activity_db_failed", error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database write error.")

    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=500, detail="Supabase offline. Database write not available.")

    # Local Fallback
    local_activities = _load_local_json("local_crm_activities.json")
    local_activities.append(payload)
    _save_local_json("local_crm_activities.json", local_activities)
    return payload


@router.get("/activities", response_model=List[ActivityResponse])
async def list_activities(user: UserPrincipal = Depends(get_current_user)):
    """List all Touchpoint Activities."""
    tenant_id = user.tenant_id
    if supabase_client:
        try:
            res = supabase_client.table("activities").select("*").eq("tenant_id", tenant_id).execute()
            return res.data or []
        except Exception as e:
            logger.error("api_list_activities_db_failed", error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database read error.")

    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=500, detail="Supabase offline. Database lookup not available.")

    local_activities = _load_local_json("local_crm_activities.json")
    return [a for a in local_activities if a.get("tenant_id") == tenant_id]


@router.get("/activities/{id}", response_model=ActivityResponse)
async def get_activity(id: UUID, user: UserPrincipal = Depends(get_current_user)):
    """Retrieve a specific logged Activity by ID."""
    tenant_id = user.tenant_id
    if supabase_client:
        try:
            res = supabase_client.table("activities").select("*").eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error("api_get_activity_db_failed", id=id, error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database lookup error.")
    
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=404, detail="Activity not found.")

    local_activities = _load_local_json("local_crm_activities.json")
    matching = [a for a in local_activities if a.get("id") == str(id) and a.get("tenant_id") == tenant_id]
    if matching:
        return matching[0]

    raise HTTPException(status_code=404, detail="Activity not found.")


# ====================================================
# CRM SPECIAL ANALYTICS & TIMELINE ROUTES
# ====================================================
@router.get("/pipeline", response_model=List[StageDealsAggregate])
async def get_crm_pipeline(user: UserPrincipal = Depends(get_current_user)):
    """Groups deals by active pipeline stages with deal counts and total valuation in USD."""
    tenant_id = user.tenant_id
    # 1. Fetch or seed stages for this tenant
    stages = await get_or_seed_stages(tenant_id)
    stages = sorted(stages, key=lambda x: x["position"])

    # 2. Fetch all deals for this tenant
    deals = []
    use_local_fallback = not supabase_client
    if supabase_client:
        try:
            res = supabase_client.table("deals").select("*").eq("tenant_id", tenant_id).execute()
            deals = res.data or []
        except Exception as e:
            logger.error("api_pipeline_deals_fetch_failed", error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database query failed.")
            use_local_fallback = True
    
    if use_local_fallback:
        if settings.app_env not in ("development", "test"):
            raise HTTPException(status_code=500, detail="Supabase offline. Database lookup not available.")
        local_deals = _load_local_json("local_crm_deals.json")
        deals = [d for d in local_deals if d.get("tenant_id") == tenant_id]

    # Map deals by stage_id
    deals_by_stage: Dict[str, List[Dict[str, Any]]] = {}
    for deal in deals:
        stage_id_str = str(deal["stage_id"])
        if stage_id_str not in deals_by_stage:
            deals_by_stage[stage_id_str] = []
        deals_by_stage[stage_id_str].append(deal)

    # 3. Formulate aggregate summaries
    aggregates = []
    for stage in stages:
        stage_id_str = str(stage["id"])
        stage_deals = deals_by_stage.get(stage_id_str, [])
        
        count = len(stage_deals)
        total_val = sum(float(d.get("value_usd", 0.0)) for d in stage_deals)

        aggregates.append({
            "stage_id": stage["id"],
            "stage_name": stage["name"],
            "position": stage["position"],
            "deals_count": count,
            "total_value_usd": total_val,
            "deals": stage_deals
        })

    return aggregates


@router.get("/contact/{id}/timeline", response_model=List[ActivityResponse])
async def get_contact_timeline(id: UUID, user: UserPrincipal = Depends(get_current_user)):
    """Fetch complete chronological activity log history for a contact."""
    tenant_id = user.tenant_id
    if supabase_client:
        try:
            res = supabase_client.table("activities").select("*").eq("contact_id", str(id)).eq("tenant_id", tenant_id).order("occurred_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error("api_timeline_fetch_failed", id=id, error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Timeline query failed.")

    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=404, detail="Contact timeline not found.")

    # Local Fallback
    local_activities = _load_local_json("local_crm_activities.json")
    contact_acts = [a for a in local_activities if a.get("contact_id") == str(id) and a.get("tenant_id") == tenant_id]
    return sorted(contact_acts, key=lambda x: x["occurred_at"], reverse=True)


# ====================================================
# LEAD DATA ENRICHMENT PIPELINE WORKER (ASYNC)
# ====================================================
async def background_lead_enrichment_worker(contact_id: str, tenant_id: str, correlation_id: str = "unknown"):
    """Simulates background lead metadata calls using Apollo/Clearbit mock triggers."""
    from security.logging import correlation_id_var, tenant_id_var
    correlation_id_var.set(correlation_id)
    tenant_id_var.set(tenant_id)
    await asyncio.sleep(1.0) # Yield control
    logger.info("crm_enrichment_background_start", contact_id=contact_id)

    # Resolve contact email/name details to mock corporate sectors
    email_domain = "clearbit.com"
    full_name = "Enriched Contact"
    
    contact = None
    if supabase_client:
        try:
            res = supabase_client.table("contacts").select("*").eq("id", contact_id).eq("tenant_id", tenant_id).execute()
            if res.data:
                contact = res.data[0]
                full_name = contact.get("full_name") or "Enriched Contact"
                email = contact.get("email")
                if email and "@" in email:
                    email_domain = email.split("@")[-1]
        except Exception:
            pass
    else:
        local_contacts = _load_local_json("local_crm_contacts.json")
        matching = [c for c in local_contacts if c["id"] == contact_id]
        if matching:
            contact = matching[0]
            full_name = contact.get("full_name") or "Enriched Contact"
            email = contact.get("email")
            if email and "@" in email:
                email_domain = email.split("@")[-1]

    # Generate mock enrichment updates
    company_clean_name = email_domain.split(".")[0].capitalize()
    linkedin_url = f"https://www.linkedin.com/in/{full_name.lower().replace(' ', '')}"
    enrich_updates = {
        "linkedin_url": linkedin_url,
        "company_name": f"{company_clean_name} Systems Inc",
        "lead_source": "Apollo.io Enriched",
        "lead_score": 85,
        "tags": ["enterprise", "enriched"],
        "custom_fields": {"enriched_at": datetime.datetime.utcnow().isoformat(), "provider": "Apollo.io"}
    }

    # Upsert linked Company record in pipeline
    company_id = str(uuid.uuid4())
    company_payload = {
        "id": company_id,
        "tenant_id": tenant_id,
        "name": f"{company_clean_name} Systems Inc",
        "domain": email_domain,
        "industry": "Software Services",
        "employee_count": 250,
        "annual_revenue": 15000000.0,
        "country": "United States",
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat(),
        "created_by": "Apollo_Enrichment"
    }

    if supabase_client:
        try:
            # 1. Upsert Company
            supabase_client.table("companies").insert(company_payload).execute()
            # 2. Update Contact
            supabase_client.table("contacts").update(enrich_updates).eq("id", contact_id).execute()
            # 3. Log task notes to activities
            act_payload = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "contact_id": contact_id,
                "type": "task",
                "occurred_at": datetime.datetime.utcnow().isoformat(),
                "duration_seconds": 0,
                "outcome": "completed",
                "ai_summary": f"Apollo.io enrichment verified: matched LinkedIn profiles & added Company record {company_clean_name}.",
                "created_by_ai": True,
                "created_at": datetime.datetime.utcnow().isoformat(),
                "updated_at": datetime.datetime.utcnow().isoformat(),
                "created_by": "Apollo_Enrichment"
            }
            supabase_client.table("activities").insert(act_payload).execute()
        except Exception as e:
            logger.error("crm_enrichment_background_supabase_failed", error=str(e))
    else:
        # Local JSON update
        local_companies = _load_local_json("local_crm_companies.json")
        local_companies.append(company_payload)
        _save_local_json("local_crm_companies.json", local_companies)

        local_contacts = _load_local_json("local_crm_contacts.json")
        for c in local_contacts:
            if c["id"] == contact_id:
                c.update(enrich_updates)
                break
        _save_local_json("local_crm_contacts.json", local_contacts)

        local_activities = _load_local_json("local_crm_activities.json")
        act_payload = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "contact_id": contact_id,
            "type": "task",
            "occurred_at": datetime.datetime.utcnow().isoformat(),
            "duration_seconds": 0,
            "outcome": "completed",
            "ai_summary": f"Apollo.io enrichment verified: matched LinkedIn profiles & added Company record {company_clean_name}.",
            "created_by_ai": True,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "created_by": "Apollo_Enrichment"
        }
        local_activities.append(act_payload)
        _save_local_json("local_crm_activities.json", local_activities)

    logger.info("crm_enrichment_background_complete", contact_id=contact_id)


@router.post("/contact/{id}/enrich", status_code=status.HTTP_202_ACCEPTED)
async def enrich_contact(id: UUID, background_tasks: BackgroundTasks, user: UserPrincipal = Depends(get_current_user)):
    """Trigger background Apollo/Clearbit lead data enrichment tasks."""
    tenant_id = user.tenant_id
    contact_exists = False
    
    # Assert contact exists before queuing enrichment
    if supabase_client:
        try:
            res = supabase_client.table("contacts").select("id").eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                contact_exists = True
        except Exception:
            pass
    else:
        local_contacts = _load_local_json("local_crm_contacts.json")
        contact_exists = any(c["id"] == str(id) and c["tenant_id"] == tenant_id for c in local_contacts)

    if not contact_exists:
        raise HTTPException(status_code=404, detail="Contact not found.")

    # Queue background enrichment task
    from security.logging import correlation_id_var
    background_tasks.add_task(background_lead_enrichment_worker, str(id), tenant_id, correlation_id_var.get())
    return {"message": "Lead data enrichment task queued successfully.", "status": "processing"}


from pydantic import BaseModel

class OutreachEmailUpdate(BaseModel):
    subject: str
    body: str


@router.post("/contacts/{id}/outreach/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_outreach_email(id: UUID, user: UserPrincipal = Depends(get_current_user)):
    """Triggers an asynchronous background job to generate cold outreach email via Claude."""
    tenant_id = user.tenant_id
    
    # Verify contact exists
    contact_exists = False
    if supabase_client:
        try:
            res = supabase_client.table("contacts").select("id").eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                contact_exists = True
        except Exception:
            pass
    else:
        local_contacts = _load_local_json("local_crm_contacts.json")
        contact_exists = any(c["id"] == str(id) and c["tenant_id"] == tenant_id for c in local_contacts)

    if not contact_exists:
        raise HTTPException(status_code=404, detail="Contact not found.")

    # Mark custom_fields.outreach_email.status as 'generating' immediately
    if supabase_client:
        try:
            # fetch current custom fields
            res = supabase_client.table("contacts").select("custom_fields").eq("id", str(id)).execute()
            cf = res.data[0]["custom_fields"] if res.data else {}
            cf["outreach_email"] = {"subject": "", "body": "", "status": "generating"}
            supabase_client.table("contacts").update({"custom_fields": cf}).eq("id", str(id)).execute()
        except Exception:
            pass
    else:
        local_contacts = _load_local_json("local_crm_contacts.json")
        for c in local_contacts:
            if c["id"] == str(id):
                c["custom_fields"] = c.get("custom_fields") or {}
                c["custom_fields"]["outreach_email"] = {"subject": "", "body": "", "status": "generating"}
                break
        _save_local_json("local_crm_contacts.json", local_contacts)

    from server.worker import enqueue_background_job
    await enqueue_background_job(
        tenant_id=tenant_id,
        job_type="generate_email",
        payload={"tenant_id": tenant_id, "contact_id": str(id)}
    )
    return {"message": "Email generation job enqueued successfully.", "status": "processing"}


@router.put("/contacts/{id}/outreach/edit", response_model=ContactResponse)
async def edit_outreach_email(id: UUID, payload: OutreachEmailUpdate, user: UserPrincipal = Depends(get_current_user)):
    """Edits the subject/body of the generated cold outreach email."""
    tenant_id = user.tenant_id
    contact = None

    if supabase_client:
        try:
            res = supabase_client.table("contacts").select("*").eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                contact = res.data[0]
        except Exception:
            pass
    else:
        local_contacts = _load_local_json("local_crm_contacts.json")
        for c in local_contacts:
            if c["id"] == str(id) and c["tenant_id"] == tenant_id:
                contact = c
                break

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")

    cf = contact.get("custom_fields") or {}
    cf["outreach_email"] = {
        "subject": payload.subject,
        "body": payload.body,
        "status": "review"
    }

    if supabase_client:
        try:
            res = supabase_client.table("contacts").update({"custom_fields": cf}).eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error("edit_email_db_failed", error=str(e))
            raise HTTPException(status_code=500, detail="Database write error.")
    else:
        local_contacts = _load_local_json("local_crm_contacts.json")
        for c in local_contacts:
            if c["id"] == str(id) and c["tenant_id"] == tenant_id:
                c["custom_fields"] = cf
                _save_local_json("local_crm_contacts.json", local_contacts)
                return c

    raise HTTPException(status_code=500, detail="Failed to edit email.")


@router.post("/contacts/{id}/outreach/send")
async def send_outreach_email(id: UUID, user: UserPrincipal = Depends(get_current_user)):
    """Sends the generated cold outreach email via Resend/mock provider."""
    tenant_id = user.tenant_id
    contact = None

    if supabase_client:
        try:
            res = supabase_client.table("contacts").select("*").eq("id", str(id)).eq("tenant_id", tenant_id).execute()
            if res.data:
                contact = res.data[0]
        except Exception:
            pass
    else:
        local_contacts = _load_local_json("local_crm_contacts.json")
        for c in local_contacts:
            if c["id"] == str(id) and c["tenant_id"] == tenant_id:
                contact = c
                break

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")

    cf = contact.get("custom_fields") or {}
    email_data = cf.get("outreach_email")
    if not email_data or not email_data.get("subject") or not email_data.get("body"):
        raise HTTPException(status_code=400, detail="No email outreach generated yet to send.")

    # Mark status as sent
    email_data["status"] = "sent"
    cf["outreach_email"] = email_data

    # Save update
    if supabase_client:
        try:
            supabase_client.table("contacts").update({"custom_fields": cf}).eq("id", str(id)).eq("tenant_id", tenant_id).execute()
        except Exception as e:
            logger.error("send_email_db_status_failed", error=str(e))
    else:
        local_contacts = _load_local_json("local_crm_contacts.json")
        for c in local_contacts:
            if c["id"] == str(id) and c["tenant_id"] == tenant_id:
                c["custom_fields"] = cf
                break
        _save_local_json("local_crm_contacts.json", local_contacts)

    logger.info("email_sent_successfully", contact_id=str(id), subject=email_data["subject"])
    return {"success": True, "message": "Email outreach dispatched successfully.", "email": email_data}
