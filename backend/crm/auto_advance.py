import os
import json
import uuid
import datetime
import asyncio
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import structlog
from server.storage_manager import supabase_client

logger = structlog.get_logger("visoora_crm")


# ====================================================
# TYPED CALL RESULT SCHEMAS
# ====================================================
class CallResult(BaseModel):
    phone_number: str = Field(..., description="E.164 target phone number")
    tenant_id: str = Field(..., description="Tenant unique identifier")
    final_state: str = Field(..., description="FSM state at call completion")
    duration_seconds: int = Field(0, description="Call duration in seconds")
    outcome: str = Field("completed", description="Outcome string, e.g. completed, no-answer")
    transcript_url: Optional[str] = Field(None, description="Public transcript URL")
    recording_url: Optional[str] = Field(None, description="Public recording URL")
    ai_summary: Optional[str] = Field(None, description="AI summary of the conversation")


# ====================================================
# LOCAL JSON FALLBACK CONTROLLERS
# ====================================================
LOCAL_CRM_DIR = "recordings"

def _load_local_json(filename: str) -> List[Dict[str, Any]]:
    os.makedirs(LOCAL_CRM_DIR, exist_ok=True)
    filepath = os.path.join(LOCAL_CRM_DIR, filename)
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except Exception:
        data = []

    if filename == "local_crm_contacts.json" and isinstance(data, list):
        modified = False
        sanitized = []
        for c in data:
            if not isinstance(c, dict):
                continue
            
            # Check and fix UUID
            id_val = c.get("id")
            is_valid_uuid = False
            if id_val:
                try:
                    uuid.UUID(str(id_val))
                    is_valid_uuid = True
                except ValueError:
                    pass
            
            if not is_valid_uuid:
                if id_val and isinstance(id_val, str):
                    c["id"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, id_val))
                else:
                    c["id"] = str(uuid.uuid4())
                modified = True

            # Backfill name/phone/company compatibility fields
            if not c.get("phone_e164") and c.get("phone_number"):
                c["phone_e164"] = c["phone_number"]
                modified = True
            elif not c.get("phone_number") and c.get("phone_e164"):
                c["phone_number"] = c["phone_e164"]
                modified = True

            if not c.get("full_name") and c.get("name"):
                c["full_name"] = c["name"]
                modified = True
            elif not c.get("name") and c.get("full_name"):
                c["name"] = c["full_name"]
                modified = True

            if not c.get("company_name") and c.get("company"):
                c["company_name"] = c["company"]
                modified = True
            elif not c.get("company") and c.get("company_name"):
                c["company"] = c["company_name"]
                modified = True

            # Ensure timestamps
            now_iso = datetime.datetime.utcnow().isoformat()
            if "created_at" not in c or not c["created_at"]:
                c["created_at"] = now_iso
                modified = True
            if "updated_at" not in c or not c["updated_at"]:
                c["updated_at"] = now_iso
                modified = True

            # Standard defaults
            if "tenant_id" not in c or not c["tenant_id"]:
                c["tenant_id"] = "acme_tenant"
                modified = True
            if "lead_score" not in c:
                c["lead_score"] = 0
                modified = True
            if "tags" not in c:
                c["tags"] = []
                modified = True
            if "custom_fields" not in c:
                c["custom_fields"] = {}
                modified = True

            sanitized.append(c)
        
        if modified:
            with open(filepath, "w") as f:
                json.dump(sanitized, f, indent=2)
        return sanitized

    return data

def _save_local_json(filename: str, data: List[Dict[str, Any]]):
    os.makedirs(LOCAL_CRM_DIR, exist_ok=True)
    filepath = os.path.join(LOCAL_CRM_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


# ====================================================
# DYNAMIC PIPELINE SEEDER
# ====================================================
DEFAULT_STAGES = [
    {"name": "New Lead", "position": 1, "probability_pct": 10, "is_terminal": False},
    {"name": "Qualified", "position": 2, "probability_pct": 30, "is_terminal": False},
    {"name": "Demo Booked", "position": 3, "probability_pct": 50, "is_terminal": False},
    {"name": "Negotiation/Demo", "position": 4, "probability_pct": 85, "is_terminal": False},
    {"name": "Stale", "position": 5, "probability_pct": 10, "is_terminal": False},
    {"name": "Closed Won", "position": 6, "probability_pct": 100, "is_terminal": True},
    {"name": "Closed Lost", "position": 7, "probability_pct": 0, "is_terminal": True},
]

async def get_or_seed_stages(tenant_id: str) -> List[Dict[str, Any]]:
    """Fetches existing pipeline stages for a tenant or seeds the standard defaults."""
    if supabase_client:
        try:
            res = supabase_client.table("pipeline_stages").select("*").eq("tenant_id", tenant_id).order("position").execute()
            if res.data:
                return res.data

            # Seed default stages
            seeded = []
            for stage in DEFAULT_STAGES:
                payload = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "name": stage["name"],
                    "position": stage["position"],
                    "probability_pct": stage["probability_pct"],
                    "is_terminal": stage["is_terminal"],
                    "created_at": datetime.datetime.utcnow().isoformat(),
                    "updated_at": datetime.datetime.utcnow().isoformat(),
                    "created_by": "AI_System"
                }
                supabase_client.table("pipeline_stages").insert(payload).execute()
                seeded.append(payload)
            logger.info("crm_stages_seeded_supabase", tenant_id=tenant_id)
            return seeded
        except Exception as e:
            logger.error("crm_stages_seed_failed", tenant_id=tenant_id, error=str(e))

    # Local Fallback seeding
    local_stages = _load_local_json("local_crm_stages.json")
    tenant_stages = [s for s in local_stages if s.get("tenant_id") == tenant_id]
    if tenant_stages:
        return sorted(tenant_stages, key=lambda x: x["position"])

    seeded = []
    for stage in DEFAULT_STAGES:
        payload = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": stage["name"],
            "position": stage["position"],
            "probability_pct": stage["probability_pct"],
            "is_terminal": stage["is_terminal"],
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "created_by": "AI_System"
        }
        local_stages.append(payload)
        seeded.append(payload)
    _save_local_json("local_crm_stages.json", local_stages)
    logger.info("crm_stages_seeded_local", tenant_id=tenant_id)
    return seeded


# ====================================================
# AUTONOMOUS PIPELINE ADVANCEMENT LOGIC
# ====================================================
async def auto_advance_deal(call_result: CallResult) -> Optional[Dict[str, Any]]:
    """
    Asynchronously processes a post-call result to advance associated CRM deals.
    Determines next pipeline stage based on call outcomes, logs histories, and updates statuses.
    """
    phone = call_result.phone_number
    tenant_id = call_result.tenant_id
    final_state = call_result.final_state
    outcome = call_result.outcome

    logger.info("crm_auto_advance_start", phone=phone, tenant_id=tenant_id, state=final_state)

    contact_id = None
    contact_name = "Valued Prospect"

    # Step 1: Find Contact by phone number and tenant ID
    if supabase_client:
        try:
            res = supabase_client.table("contacts").select("*").eq("phone_number", phone).eq("tenant_id", tenant_id).execute()
            if not res.data:
                res = supabase_client.table("contacts").select("*").eq("phone_e164", phone).eq("tenant_id", tenant_id).execute()
            if res.data:
                contact = res.data[0]
                contact_id = contact["id"]
                contact_name = contact.get("full_name") or contact.get("name") or "Valued Prospect"
        except Exception as e:
            logger.error("crm_contact_query_failed", phone=phone, error=str(e))
    else:
        local_contacts = _load_local_json("local_crm_contacts.json")
        matching = [c for c in local_contacts if c.get("tenant_id") == tenant_id and (c.get("phone_number") == phone or c.get("phone_e164") == phone)]
        if matching:
            contact = matching[0]
            contact_id = contact["id"]
            contact_name = contact.get("full_name") or contact.get("name") or "Valued Prospect"

    # If contact doesn't exist, we dynamically bootstrap contact to log activities
    if not contact_id:
        contact_id = str(uuid.uuid4())
        payload = {
            "id": contact_id,
            "tenant_id": tenant_id,
            "name": contact_name,
            "full_name": contact_name,
            "phone_number": phone,
            "phone_e164": phone,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "created_by": "AI_System"
        }
        if supabase_client:
            try:
                supabase_client.table("contacts").insert(payload).execute()
            except Exception as e:
                logger.error("crm_contact_bootstrap_failed", error=str(e))
        else:
            local_contacts = _load_local_json("local_crm_contacts.json")
            local_contacts.append(payload)
            _save_local_json("local_crm_contacts.json", local_contacts)

    # Step 2: Seed / Retrieve tenant stages
    stages = await get_or_seed_stages(tenant_id)
    stages_by_name = {s["name"]: s["id"] for s in stages}
    stages_by_id = {s["id"]: s for s in stages}

    # Target stage mapping base FSM outcomes
    target_stage_name = None
    reason = ""

    # FSM SUCCESS_COMPLETE -> Demo Booked
    if final_state == "SUCCESS_COMPLETE":
        target_stage_name = "Demo Booked"
        reason = "FSM transition to SUCCESS_COMPLETE (Demo successfully booked by AI Agent)."
    # Deal probability logic
    elif outcome == "booked":
        target_stage_name = "Negotiation/Demo"
        reason = "Outcome is booked, moved to Negotiation/Demo."
    # FSM END_CALL_DISCONNECT after QUALIFICATION -> move to Qualified
    elif final_state in ("QUALIFICATION", "BOOKING") or (final_state == "END_CALL_DISCONNECT" and outcome == "completed"):
        target_stage_name = "Qualified"
        reason = "FSM transitioned to call completion post-qualification parameters."

    # Step 3: Insert Call Activity
    activity_id = str(uuid.uuid4())
    activity_payload = {
        "id": activity_id,
        "tenant_id": tenant_id,
        "contact_id": contact_id,
        "type": "call",
        "occurred_at": datetime.datetime.utcnow().isoformat(),
        "duration_seconds": call_result.duration_seconds,
        "outcome": outcome,
        "transcript_url": call_result.transcript_url,
        "recording_url": call_result.recording_url,
        "ai_summary": call_result.ai_summary,
        "created_by_ai": True,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat(),
        "created_by": "AI_System"
    }

    if supabase_client:
        try:
            supabase_client.table("activities").insert(activity_payload).execute()
        except Exception as e:
            logger.error("crm_activity_insert_failed", error=str(e))
    else:
        local_activities = _load_local_json("local_crm_activities.json")
        local_activities.append(activity_payload)
        _save_local_json("local_crm_activities.json", local_activities)

    # Step 4: Stale check - 2+ unanswered calls
    consecutive_no_answer = 0
    if supabase_client:
        try:
            act_res = supabase_client.table("activities").select("*").eq("contact_id", contact_id).eq("type", "call").order("occurred_at", desc=True).limit(5).execute()
            activities_list = act_res.data or []
        except Exception as e:
            logger.error("crm_activities_query_failed", error=str(e))
            activities_list = []
    else:
        local_activities = _load_local_json("local_crm_activities.json")
        contact_acts = [a for a in local_activities if a.get("contact_id") == contact_id and a.get("type") == "call"]
        activities_list = sorted(contact_acts, key=lambda x: x["occurred_at"], reverse=True)

    for act in activities_list:
        if act.get("outcome") in ("no-answer", "busy", "failed"):
            consecutive_no_answer += 1
        else:
            break

    if consecutive_no_answer >= 2:
        target_stage_name = "Stale"
        reason = f"Outbound sequence recorded {consecutive_no_answer} consecutive unanswered calls."

    # Step 5: Find or create active Deal
    deal = None
    if supabase_client:
        try:
            deals_res = supabase_client.table("deals").select("*").eq("contact_id", contact_id).eq("tenant_id", tenant_id).execute()
            active_deals = [d for d in (deals_res.data or []) if not stages_by_id.get(d["stage_id"], {}).get("is_terminal", False)]
            if active_deals:
                deal = active_deals[0]
        except Exception as e:
            logger.error("crm_deal_query_failed", error=str(e))
    else:
        local_deals = _load_local_json("local_crm_deals.json")
        active_deals = [d for d in local_deals if d.get("contact_id") == contact_id and d.get("tenant_id") == tenant_id and not stages_by_id.get(d["stage_id"], {}).get("is_terminal", False)]
        if active_deals:
            deal = active_deals[0]

    # Create new deal if none active
    if not deal:
        new_deal_id = str(uuid.uuid4())
        default_stage_id = stages_by_name.get("New Lead") or stages[0]["id"]
        deal_payload = {
            "id": new_deal_id,
            "tenant_id": tenant_id,
            "contact_id": contact_id,
            "company_id": None,
            "stage_id": default_stage_id,
            "title": f"{contact_name} - Outbound Deal",
            "value_usd": 5000.0,  # Default starter value
            "currency": "USD",
            "close_date": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat(),
            "owner_id": "AI_Agent",
            "notes": "Generated autonomously upon call dial.",
            "ai_next_action": "Initial outreach call completed.",
            "ai_sentiment": "neutral",
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "created_by": "AI_System"
        }
        if supabase_client:
            try:
                supabase_client.table("deals").insert(deal_payload).execute()
                deal = deal_payload
            except Exception as e:
                logger.error("crm_deal_create_failed", error=str(e))
        else:
            local_deals = _load_local_json("local_crm_deals.json")
            local_deals.append(deal_payload)
            _save_local_json("local_crm_deals.json", local_deals)
            deal = deal_payload

    # Link the call activity to the resolved deal
    if deal:
        if supabase_client:
            try:
                supabase_client.table("activities").update({"deal_id": deal["id"]}).eq("id", activity_id).execute()
            except Exception:
                pass
        else:
            local_activities = _load_local_json("local_crm_activities.json")
            for act in local_activities:
                if act["id"] == activity_id:
                    act["deal_id"] = deal["id"]
                    break
            _save_local_json("local_crm_activities.json", local_activities)

    # Step 6: Advance Deal Stage if transition is triggered
    if deal and target_stage_name:
        target_stage_id = stages_by_name.get(target_stage_name)
        if target_stage_id and deal["stage_id"] != target_stage_id:
            from_stage_id = deal["stage_id"]
            
            # Formulate updates
            updates = {
                "stage_id": target_stage_id,
                "updated_at": datetime.datetime.utcnow().isoformat()
            }
            if target_stage_name == "Stale":
                updates["ai_next_action"] = "Manual follow-up needed"
            
            # Commit update
            if supabase_client:
                try:
                    supabase_client.table("deals").update(updates).eq("id", deal["id"]).execute()
                except Exception as e:
                    logger.error("crm_deal_update_failed", error=str(e))
            else:
                local_deals = _load_local_json("local_crm_deals.json")
                for d in local_deals:
                    if d["id"] == deal["id"]:
                        d.update(updates)
                        break
                _save_local_json("local_crm_deals.json", local_deals)

            # Insert deal stage history row
            history_id = str(uuid.uuid4())
            history_payload = {
                "id": history_id,
                "tenant_id": tenant_id,
                "deal_id": deal["id"],
                "from_stage_id": from_stage_id,
                "to_stage_id": target_stage_id,
                "reason": reason,
                "changed_by": "AI_System",
                "created_at": datetime.datetime.utcnow().isoformat(),
                "updated_at": datetime.datetime.utcnow().isoformat(),
                "created_by": "AI_System"
            }
            if supabase_client:
                try:
                    supabase_client.table("deal_stage_history").insert(history_payload).execute()
                except Exception as e:
                    logger.error("crm_history_insert_failed", error=str(e))
            else:
                local_history = _load_local_json("local_crm_stage_history.json")
                local_history.append(history_payload)
                _save_local_json("local_crm_stage_history.json", local_history)

            logger.info("crm_deal_advanced", deal_id=deal["id"], stage=target_stage_name)
            deal.update(updates)
            return deal

    return deal
