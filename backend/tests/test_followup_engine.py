import pytest
from sales_employee.followup_engine import ai_followup_engine
from sales_employee.services import StrategyDecision

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
