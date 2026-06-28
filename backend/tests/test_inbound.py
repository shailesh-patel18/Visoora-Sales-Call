import pytest
import os
import json
import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch

# Ensure backend path context is loaded
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from server.twilio_handler import app
from services.calendar import calendar_service, LOCAL_CALENDAR_FILE
from services.sms import sms_service, LOCAL_SMS_LOGS_FILE
from server.inbound_handler import (
    LOCAL_TENANTS_FILE,
    LOCAL_AGENTS_FILE,
    LOCAL_CALLBACKS_FILE,
    _init_local_files
)

client = TestClient(app)

# ----------------------------------------------------
# FIREGUARDS & TEST FIXTURES
# ----------------------------------------------------
@pytest.fixture(autouse=True)
def cleanup_local_test_files():
    """Ensures local JSON storage databases are reset before/after each test."""
    for filepath in [LOCAL_CALENDAR_FILE, LOCAL_SMS_LOGS_FILE, LOCAL_CALLBACKS_FILE]:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
                
    # Re-init files
    _init_local_files()
    calendar_service._init_local_db()
    sms_service._init_local_db()
    
    yield
    
    # Cleanup after test
    for filepath in [LOCAL_CALENDAR_FILE, LOCAL_SMS_LOGS_FILE, LOCAL_CALLBACKS_FILE]:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass


# ----------------------------------------------------
# TEST 1: TWILIO WEBHOOK ROUTE (POST /inbound-call)
# ----------------------------------------------------
def test_twilio_inbound_webhook():
    """
    Verifies that calling POST /inbound-call parses Twilio form values,
    looks up tenants, and serves standard secure Connect-Stream XML TwiML.
    """
    payload = {
        "To": "+15017122661",
        "From": "+15005550006",
        "CallSid": "CA1234567890abcdef"
    }
    
    res = client.post("/inbound-call", data=payload)
    
    assert res.status_code == 200
    assert "xml" in res.headers["content-type"]
    
    content = res.text
    assert "<Response>" in content
    assert "<Say" in content
    assert "<Connect>" in content
    assert '<Stream url="ws' in content
    assert "caller_phone=%2B15005550006" in content
    assert "<Pause length=" in content


# ----------------------------------------------------
# TEST 2: FSM NEW LEAD QUALIFICATION & AUTOMATIC BOOKING
# ----------------------------------------------------
def test_fsm_lead_qualification_and_booking():
    """
    Verifies the complete qualification path:
    INTENT_DETECTION -> QUALIFY_LEAD -> CRM Seed -> auto transition to BOOKING.
    """
    # 1. Open media stream WebSocket connection
    with client.websocket_connect("/media-stream/inbound/acme_tenant?caller_phone=%2B15005550006&company=Acme") as ws:
        
        # Turn 1: Classify intent as a New Lead Inquiry
        ws.send_text(json.dumps({
            "event": "caller_speech",
            "text": "Hello, I am interested in buying a sales calling solution for our SDR team."
        }))
        res1 = json.loads(ws.receive_text())
        assert res1["event"] == "agent_speech"
        # Should ask for name
        assert "name" in res1["text"].lower()
        
        # Turn 2: Provide Name
        ws.send_text(json.dumps({
            "event": "caller_speech",
            "text": "Steve Rogers"
        }))
        res2 = json.loads(ws.receive_text())
        assert "company" in res2["text"].lower()
        
        # Turn 3: Provide Company
        ws.send_text(json.dumps({
            "event": "caller_speech",
            "text": "Shield Enterprises"
        }))
        res3 = json.loads(ws.receive_text())
        
        # Qualified! Contact created, lead scored 85.
        # Should auto-transition to Booking slots
        assert "qualified" in res3["text"].lower()
        assert "available" in res3["text"].lower()
        assert "first" in res3["text"].lower()
        
        # Verify contact created locally
        local_contacts_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "recordings", 
            "local_crm_contacts.json"
        )
        assert os.path.exists(local_contacts_file)
        with open(local_contacts_file, "r") as f:
            contacts = json.load(f)
        assert len(contacts) >= 1
        assert contacts[-1]["full_name"] == "Steve Rogers"
        assert contacts[-1]["company_name"] == "Shield Enterprises"
        assert contacts[-1]["lead_score"] == 85
        
        # Turn 4: Accept slot 1
        ws.send_text(json.dumps({
            "event": "caller_speech",
            "text": "I will take the first slot, please."
        }))
        res4 = json.loads(ws.receive_text())
        assert "confirmed" in res4["text"].lower()
        assert res4["hangup"] is True
        
    # Verify slot is booked locally
    bookings = calendar_service._load_bookings()
    assert len(bookings) == 1
    assert bookings[0]["status"] == "confirmed"
    
    # Verify SMS confirmation dispatched
    logs = sms_service._load_sms_logs()
    assert len(logs) == 1
    assert "Steve Rogers" in logs[0]["body"]
    assert "confirmed" in logs[0]["body"]


# ----------------------------------------------------
# TEST 3: CALENDAR PREVENTS DOUBLE-BOOKING
# ----------------------------------------------------
def test_calendar_double_booking_prevention():
    """
    Asserts calendar slots book correctly and blocks double-booking.
    """
    slots = calendar_service.get_available_slots("acme_tenant", num_slots=2)
    assert len(slots) == 2
    
    target_slot = slots[0]
    
    # 1. Book first time
    evt_id = calendar_service.book_slot("acme_tenant", "contact_123", target_slot, "Demo 1")
    assert evt_id.startswith("evt_")
    
    # 2. Book second time (raises ValueError)
    with pytest.raises(ValueError) as exc:
        calendar_service.book_slot("acme_tenant", "contact_456", target_slot, "Demo 2")
    assert "already reserved" in str(exc.value)


# ----------------------------------------------------
# TEST 4: TWO-WAY SMS APPOINTMENT CANCELLATION
# ----------------------------------------------------
def test_sms_cancellation_webhook():
    """
    Verifies that incoming SMS with Body 'CANCEL' cancels appointment.
    """
    # 1. Setup a booking
    slots = calendar_service.get_available_slots("acme_tenant", num_slots=1)
    target_slot = slots[0]
    
    # Seed local contacts to map contact lookup
    local_contacts_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "recordings", 
        "local_crm_contacts.json"
    )
    with open(local_contacts_file, "w") as f:
        json.dump([
            {
                "id": "c_tony",
                "phone_e164": "+15005550006",
                "full_name": "Tony Stark",
                "tenant_id": "acme_tenant"
            }
        ], f)
        
    calendar_service.book_slot("acme_tenant", "c_tony", target_slot, "Tony Demo")
    
    # 2. Trigger Cancel SMS webhook
    sms_payload = {
        "From": "+15005550006",
        "To": "+15017122661",
        "Body": "CANCEL"
    }
    res = client.post("/api/v1/sms/incoming", data=sms_payload)
    
    assert res.status_code == 200
    assert "xml" in res.headers["content-type"]
    assert "cancelled" in res.text
    
    # Verify booking status cancelled
    bookings = calendar_service._load_bookings()
    assert len(bookings) == 1
    assert bookings[0]["status"] == "cancelled"


# ----------------------------------------------------
# TEST 5: HOT TRANSFER & CALLBACK TASK ROUTING
# ----------------------------------------------------
def test_fsm_hot_transfer_or_callback():
    """
    Verifies FSM warm human transfer paths.
    - If agent is online: play connecting dialog and return Twilio Conference.
    - If agent is offline: schedule a callback task.
    """
    # CASE A: Agent is offline (Clear local agents registry first)
    with open(LOCAL_AGENTS_FILE, "w") as f:
        json.dump([], f)
        
    with client.websocket_connect("/media-stream/inbound/acme_tenant?caller_phone=%2B15005550006") as ws:
        # Trigger Intent Triage
        ws.send_text(json.dumps({
            "event": "caller_speech",
            "text": "Connect me with support immediately."
        }))
        res = json.loads(ws.receive_text())
        assert "busy" in res["text"].lower()
        assert res["hangup"] is True
        
    # Verify callback task logged
    with open(LOCAL_CALLBACKS_FILE, "r") as f:
        callbacks = json.load(f)
    assert len(callbacks) == 1
    assert callbacks[0]["phone_number"] == "+15005550006"
    assert callbacks[0]["status"] == "pending"
    
    # CASE B: Agent is online
    with open(LOCAL_AGENTS_FILE, "w") as f:
        json.dump([
            {
                "tenant_id": "acme_tenant",
                "agent_user_id": "agent_peter",
                "agent_name": "Peter Parker",
                "is_available": True
            }
        ], f)
        
    with client.websocket_connect("/media-stream/inbound/acme_tenant?caller_phone=%2B15005550006") as ws:
        # Trigger Intent Triage
        ws.send_text(json.dumps({
            "event": "caller_speech",
            "text": "I want to talk to Olivia or any live human agent."
        }))
        res = json.loads(ws.receive_text())
        assert "transfer" in res["text"].lower()
        assert "peter parker" in res["text"].lower()
        
        # Verify transfer_action Twilio Conference
        action = res["transfer_action"]
        assert action["action"] == "conference_transfer"
        assert "conf_acme_tenant_agent_peter" in action["conference_name"]
