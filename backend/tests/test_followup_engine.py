import pytest
from sales_employee.followup_engine import ai_followup_engine
from sales_employee.services import StrategyDecision, history_service

def test_followup_engine_first_outreach():
    lead = {
        "id": "lead_123",
        "tenant_id": "test_tenant",
        "name": "Jane Doe",
        "company_name": "Cyberdyne",
        "email": "jane@cyberdyne.com",
        "phone": "+19195551234",
        "needs_review": False
    }
    history = []
    
    decision = ai_followup_engine.decide_next_action(lead, history, {})
    assert decision.action == "send_email"
    assert decision.should_send is True
    assert "initiating outreach" in decision.reason

def test_followup_engine_wait_state():
    lead = {
        "id": "lead_123",
        "tenant_id": "test_tenant",
        "name": "Jane Doe",
        "company_name": "Cyberdyne",
        "email": "jane@cyberdyne.com",
        "phone": "+19195551234",
        "needs_review": False
    }
    # Initial email sent, delivered but not opened yet
    history = [
        {"channel": "email", "direction": "outbound", "status": "sent"},
        {"channel": "email", "direction": "outbound", "status": "delivered"}
    ]
    
    decision = ai_followup_engine.decide_next_action(lead, history, {})
    assert decision.action == "wait"
    assert decision.should_send is False
    assert decision.wait_hours == 72

def test_followup_engine_high_intent_call():
    lead = {
        "id": "lead_123",
        "tenant_id": "test_tenant",
        "name": "Jane Doe",
        "company_name": "Cyberdyne",
        "email": "jane@cyberdyne.com",
        "phone": "+19195551234",
        "needs_review": False
    }
    # Initial email sent, delivered, and opened
    history = [
        {"channel": "email", "direction": "outbound", "status": "sent"},
        {"channel": "email", "direction": "outbound", "status": "delivered"},
        {"channel": "email", "direction": "outbound", "status": "opened"}
    ]
    
    decision = ai_followup_engine.decide_next_action(lead, history, {})
    assert decision.action == "call"
    assert decision.should_send is False
    assert "opened" in decision.reason

def test_followup_engine_bounce_stops_sequence():
    lead = {
        "id": "lead_123",
        "tenant_id": "test_tenant",
        "name": "Jane Doe",
        "company_name": "Cyberdyne",
        "email": "jane@cyberdyne.com",
        "phone": "+19195551234",
        "needs_review": False
    }
    history = [
        {"channel": "email", "direction": "outbound", "status": "sent"},
        {"channel": "email", "direction": "outbound", "status": "bounced"}
    ]
    
    decision = ai_followup_engine.decide_next_action(lead, history, {})
    assert decision.action == "stop_lost"
    assert decision.should_send is False
    assert "bounced" in decision.reason

def test_followup_engine_reply_escalates():
    lead = {
        "id": "lead_123",
        "tenant_id": "test_tenant",
        "name": "Jane Doe",
        "company_name": "Cyberdyne",
        "email": "jane@cyberdyne.com",
        "phone": "+19195551234",
        "needs_review": False
    }
    history = [
        {"channel": "email", "direction": "outbound", "status": "sent"},
        {"channel": "email", "direction": "inbound", "status": "replied", "metadata": {"reply_body": "Interested!"}}
    ]
    
    decision = ai_followup_engine.decide_next_action(lead, history, {})
    assert decision.action == "escalate_to_human"
    assert decision.should_send is False
    assert "replied" in decision.reason


def test_followup_engine_unsubscribe():
    lead = {
        "id": "lead_unsub",
        "tenant_id": "test_tenant",
        "name": "Bill Lumbergh",
        "company_name": "Initech",
        "email": "bill@initech.com",
        "follow_up_status": "stopped"
    }
    history = []
    
    decision = ai_followup_engine.decide_next_action(lead, history, {})
    assert decision.action == "wait"
    assert decision.should_send is False
    assert decision.wait_hours == 99999
    assert "unsubscribed" in decision.reason


def test_followup_engine_max_touches():
    lead = {
        "id": "lead_max",
        "tenant_id": "test_tenant",
        "name": "Milton Waddams",
        "company_name": "Initech",
        "email": "milton@initech.com",
        "follow_up_status": "active"
    }
    history = [
        {"channel": "email", "direction": "outbound", "status": "delivered"},
        {"channel": "email", "direction": "outbound", "status": "delivered"},
        {"channel": "email", "direction": "outbound", "status": "delivered"},
        {"channel": "email", "direction": "outbound", "status": "delivered"},
        {"channel": "email", "direction": "outbound", "status": "delivered"}
    ]
    
    decision = ai_followup_engine.decide_next_action(lead, history, {})
    assert decision.action == "stop_no_response"
    assert decision.should_send is False


def test_followup_engine_stop_on_company_reply():
    tenant_id = "test_tenant_company"
    lead1 = {
        "id": "lead_initech_1",
        "tenant_id": tenant_id,
        "name": "Peter Gibbons",
        "company_name": "Initech",
        "email": "peter@initech.com"
    }
    lead2 = {
        "id": "lead_initech_2",
        "tenant_id": tenant_id,
        "name": "Samir Nagheenanajar",
        "company_name": "Initech",
        "email": "samir@initech.com"
    }
    
    # Store leads in DB
    from sales_employee.services import store
    store.insert("leads", lead1)
    store.insert("leads", lead2)
    
    # Lead1 has an inbound reply
    history_service.add(
        tenant_id=tenant_id,
        lead_id=lead1["id"],
        channel="email",
        direction="inbound",
        status="replied",
        content_ref="msg_123"
    )
    
    # Evaluate lead2 (same company), should stop because lead1 replied
    decision = ai_followup_engine.decide_next_action(lead2, [], {})
    assert decision.action == "wait"
    assert decision.should_send is False
    assert decision.wait_hours == 99999
    assert "same company has replied" in decision.reason

