import pytest
import uuid
import datetime
import time
import os
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Adjust path context
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from server.twilio_handler import app
from crm.auto_advance import auto_advance_deal, CallResult, _load_local_json, _save_local_json

client = TestClient(app)


# ====================================================
# FIXTURES & CLEANUP
# ====================================================
@pytest.fixture(autouse=True)
def override_security_dependency():
    from security.rbac import get_current_user, UserPrincipal
    app.dependency_overrides[get_current_user] = lambda: UserPrincipal(
        user_id="test-user-id",
        email="test@test_tenant_a.com",
        role="admin",
        tenant_id="test_tenant_a",
        is_m2m=False
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def cleanup_local_crm_files():
    """Wipes active crm local JSON records to guarantee test isolation."""
    files = [
        "local_crm_contacts.json",
        "local_crm_companies.json",
        "local_crm_stages.json",
        "local_crm_deals.json",
        "local_crm_activities.json",
        "local_crm_stage_history.json"
    ]
    for filename in files:
        path = os.path.join("recordings", filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
    yield
    for filename in files:
        path = os.path.join("recordings", filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass


# ====================================================
# TEST GROUP 1: FULL CRUD REST ENDPOINTS
# ====================================================
def test_crm_contact_crud():
    """Validates full REST CRUD operations for Contacts."""
    headers = {"X-Tenant-ID": "test_tenant_a"}
    contact_payload = {
        "tenant_id": "test_tenant_a",
        "phone_e164": "+15005550001",
        "email": "sarah.connor@cyberdyne.com",
        "full_name": "Sarah Connor",
        "title": "Resistance Leader",
        "company_name": "Cyberdyne Tech",
        "linkedin_url": "https://linkedin.com/in/sarahconnor",
        "lead_source": "Cold Outreach",
        "lead_score": 90,
        "tags": ["vip", "highly-motivated"],
        "custom_fields": {"priority": "high"}
    }

    with patch("crm.router.supabase_client", None):
        # 1. CREATE
        res = client.post("/api/v1/crm/contacts", json=contact_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["full_name"] == "Sarah Connor"
        assert data["phone_e164"] == "+15005550001"
        contact_id = data["id"]

        # 2. READ LIST
        res = client.get("/api/v1/crm/contacts", headers=headers)
        assert res.status_code == 200
        contacts_list = res.json()
        assert len(contacts_list) == 1
        assert contacts_list[0]["id"] == contact_id

        # 3. READ BY ID
        res = client.get(f"/api/v1/crm/contacts/{contact_id}", headers=headers)
        assert res.status_code == 200
        assert res.json()["title"] == "Resistance Leader"

        # 4. UPDATE
        update_payload = {"title": "General of Resistance", "lead_score": 95}
        res = client.put(f"/api/v1/crm/contacts/{contact_id}", json=update_payload, headers=headers)
        assert res.status_code == 200
        assert res.json()["title"] == "General of Resistance"
        assert res.json()["lead_score"] == 95

        # 5. DELETE
        res = client.delete(f"/api/v1/crm/contacts/{contact_id}", headers=headers)
        assert res.status_code == 204

        # Read after delete must return 404
        res = client.get(f"/api/v1/crm/contacts/{contact_id}", headers=headers)
        assert res.status_code == 404


def test_crm_deal_crud():
    """Validates complete CRUD REST operations for Deals."""
    headers = {"X-Tenant-ID": "test_tenant_a"}
    deal_payload = {
        "tenant_id": "test_tenant_a",
        "stage_id": str(uuid.uuid4()),
        "title": "Sarah Connor - Enterprise Upgrade",
        "value_usd": 75000.0,
        "currency": "USD",
        "owner_id": "AI_Agent",
        "notes": "Keen interest in secure VAD orchestration.",
        "ai_sentiment": "positive"
    }

    with patch("crm.router.supabase_client", None):
        # 1. CREATE
        res = client.post("/api/v1/crm/deals", json=deal_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Sarah Connor - Enterprise Upgrade"
        assert data["value_usd"] == 75000.0
        deal_id = data["id"]

        # 2. READ LIST
        res = client.get("/api/v1/crm/deals", headers=headers)
        assert res.status_code == 200
        deals_list = res.json()
        assert len(deals_list) == 1
        assert deals_list[0]["id"] == deal_id

        # 3. UPDATE
        update_payload = {"value_usd": 85000.0, "ai_sentiment": "positive"}
        res = client.put(f"/api/v1/crm/deals/{deal_id}", json=update_payload, headers=headers)
        assert res.status_code == 200
        assert res.json()["value_usd"] == 85000.0

        # 4. DELETE
        res = client.delete(f"/api/v1/crm/deals/{deal_id}", headers=headers)
        assert res.status_code == 204


# ====================================================
# TEST GROUP 2: AUTONOMOUS STAGE PROGRESSIONS
# ====================================================
@pytest.mark.asyncio
async def test_auto_advance_success_complete():
    """Asserts FSM SUCCESS_COMPLETE successfully advances deals to 'Demo Booked'."""
    tenant = "tenant_adv"
    phone = "+15005550002"

    call_res = CallResult(
        phone_number=phone,
        tenant_id=tenant,
        final_state="SUCCESS_COMPLETE",
        duration_seconds=45,
        outcome="completed",
        ai_summary="Successfully booked deep-dive demo."
    )

    with patch("crm.auto_advance.supabase_client", None):
        # Trigger progression (bootstraps contact and deal under standard pipeline flow)
        deal = await auto_advance_deal(call_res)
        
        # Load local stages to match UUID
        stages = _load_local_json("local_crm_stages.json")
        demo_stage = [s for s in stages if s["name"] == "Demo Booked" and s["tenant_id"] == tenant][0]
        
        assert deal is not None
        assert deal["stage_id"] == demo_stage["id"]

        # Check history is populated
        history = _load_local_json("local_crm_stage_history.json")
        assert len(history) == 1
        assert history[0]["deal_id"] == deal["id"]
        assert history[0]["to_stage_id"] == demo_stage["id"]
        assert "SUCCESS_COMPLETE" in history[0]["reason"]


@pytest.mark.asyncio
async def test_auto_advance_qualification():
    """Asserts FSM END_CALL_DISCONNECT after QUALIFICATION moves deal to 'Qualified'."""
    tenant = "tenant_adv"
    phone = "+15005550003"

    call_res = CallResult(
        phone_number=phone,
        tenant_id=tenant,
        final_state="QUALIFICATION",
        duration_seconds=30,
        outcome="completed",
        ai_summary="Prospect qualified budget and needs."
    )

    with patch("crm.auto_advance.supabase_client", None):
        deal = await auto_advance_deal(call_res)
        stages = _load_local_json("local_crm_stages.json")
        qualified_stage = [s for s in stages if s["name"] == "Qualified" and s["tenant_id"] == tenant][0]

        assert deal is not None
        assert deal["stage_id"] == qualified_stage["id"]


@pytest.mark.asyncio
async def test_auto_advance_stale_consecutive_no_answers():
    """Asserts 2+ unanswered calls moves the deal to 'Stale' with follow-up task."""
    tenant = "tenant_adv"
    phone = "+15005550004"

    call_res_1 = CallResult(
        phone_number=phone,
        tenant_id=tenant,
        final_state="INITIATION",
        duration_seconds=0,
        outcome="no-answer"
    )

    call_res_2 = CallResult(
        phone_number=phone,
        tenant_id=tenant,
        final_state="INITIATION",
        duration_seconds=0,
        outcome="no-answer"
    )

    with patch("crm.auto_advance.supabase_client", None):
        # 1st call no answer
        deal_1 = await auto_advance_deal(call_res_1)
        stages = _load_local_json("local_crm_stages.json")
        new_lead_stage = [s for s in stages if s["name"] == "New Lead" and s["tenant_id"] == tenant][0]
        assert deal_1["stage_id"] == new_lead_stage["id"]

        # 2nd call no answer
        deal_2 = await auto_advance_deal(call_res_2)
        stale_stage = [s for s in stages if s["name"] == "Stale" and s["tenant_id"] == tenant][0]
        
        assert deal_2["stage_id"] == stale_stage["id"]
        assert deal_2["ai_next_action"] == "Manual follow-up needed"


# ====================================================
# TEST GROUP 3: SPECIALIZED ANALYTICS & TIMELINE ENDPOINTS
# ====================================================
def test_crm_pipeline_aggregator():
    """Validates GET /crm/pipeline groups deals and valuations accurately."""
    headers = {"X-Tenant-ID": "test_tenant_a"}
    
    with patch("crm.router.supabase_client", None), patch("crm.auto_advance.supabase_client", None):
        # 1. Register Contact
        contact_res = client.post("/api/v1/crm/contacts", json={
            "phone_e164": "+15005551000",
            "email": "tony.stark@stark.com",
            "full_name": "Tony Stark",
            "tenant_id": "test_tenant_a"
        })
        contact_id = contact_res.json()["id"]

        # Seeding Default Stages
        client.get("/api/v1/crm/pipeline", headers=headers)
        stages = _load_local_json("local_crm_stages.json")
        stage_map = {s["name"]: s["id"] for s in stages if s["tenant_id"] == "test_tenant_a"}

        # 2. Register two deals under "Demo Booked"
        client.post("/api/v1/crm/deals", json={
            "contact_id": contact_id,
            "stage_id": stage_map["Demo Booked"],
            "title": "Arc Reactor Expansion",
            "value_usd": 50000.0,
            "currency": "USD",
            "tenant_id": "test_tenant_a"
        })

        client.post("/api/v1/crm/deals", json={
            "contact_id": contact_id,
            "stage_id": stage_map["Demo Booked"],
            "title": "Jarvis Integration",
            "value_usd": 30000.0,
            "currency": "USD",
            "tenant_id": "test_tenant_a"
        })

        # 3. Retrieve Pipeline summaries
        res = client.get("/api/v1/crm/pipeline", headers=headers)
        assert res.status_code == 200
        pipeline = res.json()
        
        # Verify Demo Booked aggregated values
        demo_booked_group = [group for group in pipeline if group["stage_name"] == "Demo Booked"][0]
        assert demo_booked_group["deals_count"] == 2
        assert demo_booked_group["total_value_usd"] == 80000.0


def test_crm_contact_timeline_and_enrichment():
    """Validates GET timeline and POST enrich background execution."""
    headers = {"X-Tenant-ID": "test_tenant_a"}

    with patch("crm.router.supabase_client", None), patch("crm.auto_advance.supabase_client", None):
        # 1. Register Contact
        contact_res = client.post("/api/v1/crm/contacts", json={
            "phone_e164": "+15005552000",
            "email": "elon@spacex.com",
            "full_name": "Elon Musk",
            "tenant_id": "test_tenant_a"
        })
        contact_id = contact_res.json()["id"]

        # 2. Log mock Call Activity
        client.post("/api/v1/crm/activities", json={
            "contact_id": contact_id,
            "type": "call",
            "duration_seconds": 120,
            "outcome": "demo_booked",
            "ai_summary": "Talked Mars landing, booked demo.",
            "tenant_id": "test_tenant_a"
        })

        # 3. Check Timeline
        res = client.get(f"/api/v1/crm/contact/{contact_id}/timeline", headers=headers)
        assert res.status_code == 200
        timeline = res.json()
        assert len(timeline) == 1
        assert timeline[0]["type"] == "call"
        assert timeline[0]["outcome"] == "demo_booked"

        # 4. Trigger Lead enrichment (Apollo/Clearbit)
        res = client.post(f"/api/v1/crm/contact/{contact_id}/enrich", headers=headers)
        assert res.status_code == 202
        assert res.json()["status"] == "processing"
        
        # Manually invoke background enrichment to assert details (since TestClient is blocking)
        from crm.router import background_lead_enrichment_worker
        import asyncio
        asyncio.run(background_lead_enrichment_worker(contact_id, "test_tenant_a"))

        # Verify contact details are enriched
        res = client.get(f"/api/v1/crm/contacts/{contact_id}", headers=headers)
        assert res.status_code == 200
        enriched = res.json()
        assert enriched["lead_score"] == 85
        assert enriched["lead_source"] == "Apollo.io Enriched"
        assert "enriched" in enriched["tags"]
        assert enriched["linkedin_url"] == "https://www.linkedin.com/in/elonmusk"
