import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from server.twilio_handler import app
from sales_employee.services import (
    AgentCreate,
    LeadCreate,
    email_generation_service,
    history_service,
    knowledge_service,
    store,
    strategy_engine,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_security_dependency():
    from security.rbac import get_current_user, UserPrincipal

    app.dependency_overrides[get_current_user] = lambda: UserPrincipal(
        user_id="phase-a-user",
        email="phase-a@test.com",
        role="admin",
        tenant_id="phase_a_tenant",
        is_m2m=False,
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def cleanup_phase_a_files():
    for filename in store.table_files.values():
        path = os.path.join("recordings", filename)
        if os.path.exists(path):
            os.remove(path)
    yield
    for filename in store.table_files.values():
        path = os.path.join("recordings", filename)
        if os.path.exists(path):
            os.remove(path)


def test_agent_knowledge_retrieval_and_call_context_shared():
    tenant = "phase_a_tenant"
    agent = knowledge_service.create_agent(
        tenant,
        AgentCreate(
            name="Enterprise SDR",
            persona_config={
                "agent_name": "Maya",
                "company_name": "Visoora",
                "tone": "direct",
                "value_proposition": "reduce lead response time",
            },
        ),
    )
    knowledge_service.ingest_text(
        tenant,
        agent["id"],
        "pricing.txt",
        "Visoora offers premium onboarding and a compliance-first outbound engine for regulated sales teams.",
    )

    chunks = knowledge_service.retrieve(tenant, agent["id"], "regulated compliance onboarding")
    assert chunks
    assert "compliance-first" in chunks[0]["chunk_text"]

    from pipeline.states import StateMachineController

    fsm = StateMachineController({"name": "Sam", "company": "Acme", "agent_id": agent["id"]}, tenant_id=tenant)
    prompt = fsm.compile_expert_system_prompt()
    assert "Maya" in prompt
    assert "AGENT SALES BRAIN" in prompt
    assert "compliance-first" in prompt


@pytest.mark.asyncio
async def test_lead_research_broken_url_fails_closed_needs_review():
    tenant = "phase_a_tenant"
    lead = LeadCreate(
        agent_id="agent_1",
        name="Dana",
        company_name="Broken Co",
        website="https://broken.example",
        email="dana@other.example",
        phone="+15005550111",
    )
    with patch("sales_employee.services.httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value.get = AsyncMock(side_effect=RuntimeError("dead website"))
        created = await __import__("sales_employee.services", fromlist=["create_lead_and_research"]).create_lead_and_research(tenant, lead)

    assert created["needs_review"] is True
    assert created["research_confidence"] == 0.0
    assert created["research_brief"]["domain_mismatches"]


def test_strategy_engine_branches_are_explicit_and_logged():
    tenant = "phase_a_tenant"
    lead = {"id": "lead_1", "tenant_id": tenant, "needs_review": False}

    first = strategy_engine.decide_next_action(lead, [], {})
    assert first.action == "send_email_now"
    assert first.reason

    reply = strategy_engine.decide_next_action(lead, [{"channel": "email", "direction": "inbound", "status": "replied"}], {})
    assert reply.action == "escalate_to_human"

    opened = strategy_engine.decide_next_action(lead, [{"channel": "email", "direction": "outbound", "status": "opened"}], {})
    assert opened.action == "retry_call"

    no_answer = strategy_engine.decide_next_action(lead, [{"channel": "call", "direction": "outbound", "status": "no-answer"}], {})
    assert no_answer.action == "send_email_referencing_prior_call"

    stop = strategy_engine.decide_next_action(
        lead,
        [{"channel": "email", "direction": "outbound", "status": "delivered"} for _ in range(5)],
        {},
    )
    assert stop.action == "mark_no_response_stop"
    logged = strategy_engine.log_decision(tenant, lead["id"], stop)
    assert logged["tenant_id"] == tenant
    assert logged["reason"] == stop.reason


def test_email_generation_uses_lead_research_and_history():
    tenant = "phase_a_tenant"
    agent = knowledge_service.create_agent(
        tenant,
        AgentCreate(name="Agent", persona_config={"agent_name": "Riya", "value_proposition": "book qualified demos"}),
    )
    knowledge_service.ingest_text(tenant, agent["id"], "sales.txt", "Use the healthcare ROI proof point when relevant.")
    lead_a = {
        "agent_id": agent["id"],
        "name": "Priya",
        "company_name": "CareOps",
        "research_brief": {"personalization_hooks": ["healthcare scheduling"]},
    }
    lead_b = {
        "agent_id": agent["id"],
        "name": "Max",
        "company_name": "FactoryOS",
        "research_brief": {"personalization_hooks": ["manufacturing handoffs"]},
    }

    draft_a = email_generation_service.generate(tenant, agent["id"], lead_a, [{"channel": "call"}])
    draft_b = email_generation_service.generate(tenant, agent["id"], lead_b, [])

    assert "tried calling" in draft_a.body
    assert "healthcare scheduling" in draft_a.body
    assert "manufacturing handoffs" in draft_b.body
    assert draft_a.body != draft_b.body


def test_sales_employee_endpoints_require_tenant_and_write_reply_history():
    agent_res = client.post(
        "/api/v1/sales-employee/agents",
        json={"name": "Missing Tenant", "persona_config": {}},
    )
    assert agent_res.status_code == 422

    headers = {"X-Tenant-ID": "phase_a_tenant"}
    agent_res = client.post(
        "/api/v1/sales-employee/agents",
        json={"name": "Phase A Agent", "persona_config": {"agent_name": "Asha"}},
        headers=headers,
    )
    assert agent_res.status_code == 201
    agent_id = agent_res.json()["id"]

    client.post(
        f"/api/v1/sales-employee/agents/{agent_id}/knowledge/text",
        json={"source_file": "brief.txt", "text": "Asha sells compliance-safe AI sales follow-up."},
        headers=headers,
    )

    lead_payload = {
        "agent_id": agent_id,
        "name": "Taylor",
        "company_name": "Example",
        "website": "https://example.com",
        "email": "taylor@example.com",
        "phone": "+15005550123",
    }
    with patch("sales_employee.services.httpx.AsyncClient") as client_cls:
        response = AsyncMock()
        response.text = "<html><body>Example builds scheduling software for sales teams.</body></html>"
        response.raise_for_status = Mock(return_value=None)
        client_cls.return_value.__aenter__.return_value.get = AsyncMock(return_value=response)
        lead_res = client.post("/api/v1/sales-employee/leads", json=lead_payload, headers=headers)
    assert lead_res.status_code == 201
    lead_id = lead_res.json()["id"]
    assert lead_res.json()["needs_review"] is False

    reply_res = client.post(
        "/api/v1/sales-employee/webhooks/email/replies",
        json={"lead_id": lead_id, "message_id": "msg_1", "text": "Interested"},
        headers=headers,
    )
    assert reply_res.status_code == 200
    assert reply_res.json()["status"] == "replied"

    decision_res = client.post(f"/api/v1/sales-employee/leads/{lead_id}/decide", headers=headers)
    assert decision_res.status_code == 200
    assert decision_res.json()["action"] == "escalate_to_human"

    timeline = history_service.list_for_lead("phase_a_tenant", lead_id)
    assert len(timeline) == 1
    assert timeline[0]["channel"] == "email"
