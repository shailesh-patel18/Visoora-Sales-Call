import pytest
import time
import uuid
import json
import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch, mock_open
from fastapi.testclient import TestClient

# Ensure backend path loading
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from server.twilio_handler import app
from security.config import settings
from security.rbac import UserPrincipal
from compliance.gate import (
    get_calling_hours_status,
    verify_compliance_gate,
    get_tenant_compliance_settings,
    DNCBlockedException,
    OutsideCallingHoursException,
    ConsentRequiredException,
    LOCAL_DNC_FILE,
    LOCAL_CONSENT_FILE,
    LOCAL_COMPLIANCE_SETTINGS_FILE
)

client = TestClient(app)

# ----------------------------------------------------
# COMPLIANCE REGULATION REFERENCE CITATIONS
# ----------------------------------------------------
# 1. DNC Check: Enforces compliance with TCPA 47 U.S.C. § 227(c) and FCC 47 CFR § 64.1200(c).
# 2. Timezone calling hours: Enforces FCC calling hours limits under 47 CFR § 64.1200(e)(1).
# 3. Prior Express Consent: Enforces GDPR Article 7, FCC 47 CFR § 64.1200(a)(2), and FTC TSR 16 CFR § 310.4.
# 4. Recording Disclosure: Enforces Federal Wiretap Act 18 U.S.C. § 2511 and State Two-Party Consent rules.
# 5. AI disclosure: Enforces FTC Telemarketing Sales Rule automated identifiers (FTC 16 CFR Part 310).

# Helper for secure M2M header injection
def get_admin_headers() -> dict:
    settings.system_api_keys.add("key_compliance_qa_testing")
    return {"X-API-Key": "key_compliance_qa_testing"}

# Helper to mock specific compliance files selectively
def mock_open_for_compliance(dnc_data=None, consent_data=None, settings_data=None):
    import builtins
    original_open = builtins.open
    
    dnc_json = json.dumps(dnc_data or [])
    consent_json = json.dumps(consent_data or [])
    settings_json = json.dumps(settings_data or {})
    
    def side_effect(file, *args, **kwargs):
        file_str = str(file)
        if "local_dnc.json" in file_str:
            return mock_open(read_data=dnc_json)()
        elif "local_consents.json" in file_str:
            return mock_open(read_data=consent_json)()
        elif "local_tenant_compliance.json" in file_str:
            return mock_open(read_data=settings_json)()
        return original_open(file, *args, **kwargs)
        
    return patch("builtins.open", side_effect=side_effect)

# ----------------------------------------------------
# TEST GROUP 1: DO NOT CALL (DNC) CHECKS
# ----------------------------------------------------
@pytest.mark.asyncio
async def test_dnc_block_registry():
    """
    Asserts phone number listed on the tenant's registry raises a DNCBlockedException.
    Statute: TCPA 47 U.S.C. § 227(c) / FCC 47 CFR § 64.1200(c).
    """
    blocked_phone = "+15017122661"
    tenant_id = "acme_corp"
    
    # Pre-populate local DNC fallback file with blocked record
    test_dnc_record = [{"phone_number": blocked_phone, "tenant_id": tenant_id}]
    
    with mock_open_for_compliance(dnc_data=test_dnc_record):
        with patch("compliance.gate.get_calling_hours_status", return_value=(True, "America/New_York", "10:00 AM", "2026-05-24T10:00:00")):
            with pytest.raises(DNCBlockedException) as exc_info:
                await verify_compliance_gate(blocked_phone, tenant_id, str(uuid.uuid4()))
                
            assert "DNC_BLOCKED" in str(exc_info.value.invalid_params[0]["reason"])

def test_dnc_add_and_remove_endpoints():
    """
    Asserts POST /compliance/dnc/add and DELETE /compliance/dnc/remove enlist and delist phone numbers.
    """
    headers = get_admin_headers()
    test_phone = "+15005550006"
    
    # 1. Add to DNC
    add_res = client.post("/compliance/dnc/add", json={"phone_number": test_phone}, headers=headers)
    assert add_res.status_code == 200
    assert add_res.json()["action"] == "added_to_dnc"
    
    # 2. Remove from DNC
    del_res = client.request("DELETE", "/compliance/dnc/remove", json={"phone_number": test_phone}, headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["action"] == "removed_from_dnc"
    
    # Clean system keys
    settings.system_api_keys.discard("key_compliance_qa_testing")

# ----------------------------------------------------
# TEST GROUP 2: TIMEZONE CALLING HOUR ENFORCEMENTS
# ----------------------------------------------------
def test_calling_hours_compliance_gate():
    """
    Asserts that get_calling_hours_status properly maps numbers to timezones and blocks outside 8 AM - 9 PM.
    Statute: FCC Calling Hours Rules 47 CFR § 64.1200(e)(1).
    """
    # Test valid US New York number (+1212)
    phone = "+12125550199"
    
    with patch("phonenumbers.timezone.time_zones_for_number", return_value=("America/New_York",)):
        # Case A: Mock time in New York at 10:00 AM (Allowed)
        mock_tz_time = datetime.datetime(2026, 5, 24, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_tz_time
            is_allowed, tz_name, time_str, next_window = get_calling_hours_status(phone)
            assert is_allowed is True
            assert tz_name == "America/New_York"
            
        # Case B: Mock time in New York at 10:00 PM (Blocked)
        mock_tz_time_late = datetime.datetime(2026, 5, 24, 22, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_tz_time_late
            is_allowed, tz_name, time_str, next_window = get_calling_hours_status(phone)
            assert is_allowed is False
            # Next window should be tomorrow at 8:00 AM
            assert "08:00:00" in next_window

# ----------------------------------------------------
# TEST GROUP 3: PRIOR EXPRESS WRITTEN CONSENT (PEWC)
# ----------------------------------------------------
@pytest.mark.asyncio
async def test_consent_token_missing_raises_exception():
    """
    Statute: FCC 47 CFR § 64.1200(a)(2) / FTC TSR 16 CFR § 310.4.
    """
    with patch("compliance.gate.get_calling_hours_status", return_value=(True, "America/New_York", "10:00 AM", "2026-05-24T10:00:00")):
        with pytest.raises(ConsentRequiredException) as exc_info:
            await verify_compliance_gate("+12025550143", "acme_tenant", consent_token=None)
        assert "consent_token is missing" in str(exc_info.value.invalid_params[0]["detail"])

@pytest.mark.asyncio
async def test_consent_token_mismatched_phone():
    """
    Token registered to a different number must be rejected.
    """
    token = str(uuid.uuid4())
    tenant_id = "acme_tenant"
    
    # Token matches another number
    consent_record = [{
        "consent_token": token,
        "phone_number": "+15559999999", # Other number
        "tenant_id": tenant_id,
        "expires_at": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).isoformat()
    }]
    
    with mock_open_for_compliance(consent_data=consent_record):
        with patch("compliance.gate.get_calling_hours_status", return_value=(True, "America/New_York", "10:00 AM", "2026-05-24T10:00:00")):
            with pytest.raises(ConsentRequiredException) as exc_info:
                await verify_compliance_gate("+12025550143", tenant_id, token)
            assert "different phone number" in str(exc_info.value.invalid_params[0]["detail"])

@pytest.mark.asyncio
async def test_consent_token_expired():
    """
    Token with past expiration (beyond 90 days FTC window) must be rejected.
    """
    token = str(uuid.uuid4())
    phone = "+12025550143"
    tenant_id = "acme_tenant"
    
    # Token expired yesterday
    consent_record = [{
        "consent_token": token,
        "phone_number": phone,
        "tenant_id": tenant_id,
        "expires_at": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()
    }]
    
    with mock_open_for_compliance(consent_data=consent_record):
        with patch("compliance.gate.get_calling_hours_status", return_value=(True, "America/New_York", "10:00 AM", "2026-05-24T10:00:00")):
            with pytest.raises(ConsentRequiredException) as exc_info:
                await verify_compliance_gate(phone, tenant_id, token)
            assert "expired" in str(exc_info.value.invalid_params[0]["detail"])

# ----------------------------------------------------
# TEST GROUP 4: TwiML DISCLOSURE ANNUNCIATIONS
# ----------------------------------------------------
def test_twiml_disclosure_injections():
    """
    Asserts that the /incoming-call webhook dynamically injects Say tags
    under specific recording and AI disclosure configurations.
    Statutes: Wiretap Act 18 U.S.C. § 2511 & FTC AI Guidelines.

    Rec 5 note: verify_twilio_signature mock bypass now requires BOTH
    the placeholder token AND APP_ENV=test. We patch the env accordingly.
    """
    import os
    from unittest.mock import patch

    tenant_id = "acme_compliance_settings"

    # 1. Enable Recording + AI Disclosures
    settings_mock = {
        tenant_id: {
            "recording_disclosure_enabled": True,
            "recording_disclosure_text": "This call is recorded.",
            "ai_disclosure_enabled": True,
            "ai_disclosure_text": "You speak with a robot on behalf of [Company]."
        }
    }

    with mock_open_for_compliance(settings_data=settings_mock):
        # Rec 5 hardening: mock bypass requires APP_ENV=test AND placeholder token.
        # Both conditions are explicitly set here to exercise the test-only bypass path.
        settings.twilio_auth_token = "mock"
        with patch.dict(os.environ, {"APP_ENV": "test"}):
            headers = {"X-Twilio-Signature": "any_signature"}
            url = f"/incoming-call?phone=%2B1212&name=Alice&company=WayneCorp&tenant_id={tenant_id}"

            response = client.post(url, headers=headers)
            assert response.status_code == 200

            # Verify XML announcements
            xml_content = response.text
            assert "<Say" in xml_content
            assert "This call is recorded." in xml_content
            assert "WayneCorp" in xml_content  # Replaces [Company] dynamically
            assert "robot" in xml_content
            assert "<Connect>" in xml_content  # Bridges to media websocket stream after TTS disclosure
