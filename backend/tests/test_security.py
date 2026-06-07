import pytest
import time
import uuid
import jwt
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

# Adjust path context
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from server.twilio_handler import app
from security.config import settings
from security.errors import AuthenticationException, AuthorizationException
from security.rate_limiter import rate_limiter

# Initialize FastAPI test client
client = TestClient(app)

# Helper function to generate mock payload
def get_mock_jwt_payload(role: str = "viewer", tenant_id: str = "acme_tenant", email: str = "user@acme.com") -> dict:
    return {
        "sub": str(uuid.uuid4()),
        "email": email,
        "role": role,
        "tenant_id": tenant_id,
        "exp": int(time.time()) + 3600,
        "aud": "authenticated"
    }

# ----------------------------------------------------
# TEST GROUP 1: PUBLIC HEALTH PATHWAY
# ----------------------------------------------------
def test_health_endpoint_public():
    """
    Asserts that the /health check endpoint is unrestricted and passes without credentials.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

# ----------------------------------------------------
# TEST GROUP 2: AUTHENTICATION AND HEADER MISSES
# ----------------------------------------------------
def test_endpoint_missing_credentials_returns_rfc7807():
    """
    Asserts that requests without Bearer tokens or API keys receive 401 Problem Details responses.
    """
    response = client.get("/api/campaigns")
    assert response.status_code == 401
    payload = response.json()
    assert payload["type"] == "https://visoora.com/errors/unauthenticated"
    assert payload["title"] == "Authentication Failed"
    assert payload["status"] == 401
    assert "Authentication required" in payload["detail"]
    assert payload["instance"] == "/api/campaigns"

@patch("security.rbac.verify_supabase_jwt")
def test_endpoint_expired_token_returns_rfc7807(mock_verify):
    """
    Asserts expired JWT token validation returns standard Bearer error messages.
    """
    # Force verify_supabase_jwt to raise expired token exception
    mock_verify.side_effect = AuthenticationException("Session expired. Please log in again.")
    
    headers = {"Authorization": "Bearer expired_token_bytes"}
    response = client.get("/api/campaigns", headers=headers)
    assert response.status_code == 401
    payload = response.json()
    assert payload["type"] == "https://visoora.com/errors/unauthenticated"
    assert "Session expired" in payload["detail"]

# ----------------------------------------------------
# TEST GROUP 3: RBAC ROLE BOUNDARIES
# ----------------------------------------------------
@patch("security.rbac.verify_supabase_jwt")
def test_rbac_viewer_role_blocked_from_campaign_add(mock_verify):
    """
    Viewer role should be forbidden from writing campaign leads (admin only).
    """
    mock_verify.return_value = get_mock_jwt_payload(role="viewer")
    
    headers = {"Authorization": "Bearer valid_jwt_token"}
    response = client.post("/api/campaigns/add", headers=headers, json={"name": "Alice"})
    
    assert response.status_code == 403
    payload = response.json()
    assert payload["type"] == "https://visoora.com/errors/forbidden"
    assert payload["title"] == "Forbidden Access"
    assert "viewer" in payload["detail"]

@patch("compliance.gate.verify_compliance_gate", new_callable=AsyncMock)
@patch("security.rbac.verify_supabase_jwt")
def test_rbac_agent_role_can_dial_but_not_add_leads(mock_verify, mock_compliance):
    """
    Agent role should be permitted to trigger dials but forbidden from creating new leads.
    """
    # 1. Block from adding leads
    mock_verify.return_value = get_mock_jwt_payload(role="agent")
    headers = {"Authorization": "Bearer valid_jwt_token"}
    
    add_res = client.post("/api/campaigns/add", headers=headers, json={"name": "Alice"})
    assert add_res.status_code == 403
    
    # 2. Allow dialing campaigns
    dial_res = client.post("/api/campaigns/dial", headers=headers, json={"id": "lead_1"})
    # It passes auth, but lead will not be found in local list (returning success: false or not found, status 200/404)
    assert dial_res.status_code in [200, 201, 404]

@patch("security.rbac.verify_supabase_jwt")
def test_rbac_admin_role_can_perform_all_actions(mock_verify):
    """
    Admin role must possess complete system clearance.
    """
    mock_verify.return_value = get_mock_jwt_payload(role="admin")
    headers = {"Authorization": "Bearer valid_jwt_token"}
    
    add_res = client.post("/api/campaigns/add", headers=headers, json={"name": "Alice"})
    # Should perform writing logic instead of returning 403
    assert add_res.status_code == 200

# ----------------------------------------------------
# TEST GROUP 4: MACHINE-TO-MACHINE (M2M) API KEYS
# ----------------------------------------------------
def test_m2m_valid_api_key_bypasses_jwt():
    """
    M2M API keys in SYSTEM_API_KEYS should be allowed bypass access.
    """
    # Inject a system key into temporary test settings
    settings.system_api_keys.add("key_test_prod_12345")
    
    headers = {"X-API-Key": "key_test_prod_12345"}
    response = client.get("/api/campaigns", headers=headers)
    assert response.status_code == 200
    
    # Clean settings key
    settings.system_api_keys.discard("key_test_prod_12345")

# ----------------------------------------------------
# TEST GROUP 5: TWILIO WEBHOOK SIGNATURES
# ----------------------------------------------------
def test_twilio_webhook_missing_signature_rejected():
    """
    Asserts missing Twilio signature header on webhooks is blocked with 401 status.
    """
    response = client.post("/incoming-call", data={"CallSid": "CA123"})
    assert response.status_code == 401
    assert "Missing Twilio signature" in response.json()["detail"]

# ----------------------------------------------------
# TEST GROUP 6: TENANT-BASED RATE LIMITING
# ----------------------------------------------------
@pytest.mark.asyncio
async def test_rate_limiter_concurrency_breach():
    """
    Validates rate limiter blocks request when 10 concurrent slots are filled.
    """
    tenant_id = "test_tenant_a"
    rate_limiter.redis_url = "" # Force local fallback for fast testing
    await rate_limiter.connect()
    
    # Fill up 10 slots
    for i in range(10):
        res = await rate_limiter.acquire_call(tenant_id, f"call_sid_{i}")
        assert res is True
        
    # Attempt 11th acquisition
    with pytest.raises(Exception) as exc_info:
        await rate_limiter.acquire_call(tenant_id, "call_sid_11")
    assert "10 concurrent active calls" in str(exc_info.value)
    
    # Release one slot and re-attempt
    await rate_limiter.release_call(tenant_id, "call_sid_0")
    res = await rate_limiter.acquire_call(tenant_id, "call_sid_11")
    assert res is True
    
    # Clean up all slots
    for i in range(1, 12):
        await rate_limiter.release_call(tenant_id, f"call_sid_{i}")

@pytest.mark.asyncio
async def test_rate_limiter_daily_breach():
    """
    Validates daily quota threshold blocks requests beyond 500.
    """
    tenant_id = "test_tenant_b"
    rate_limiter.redis_url = "" # Force local fallback
    await rate_limiter.connect()
    
    # Fake daily list containing 500 timestamps
    rate_limiter._local_daily[tenant_id] = [time.time()] * 500
    
    with pytest.raises(Exception) as exc_info:
        await rate_limiter.acquire_call(tenant_id, "call_sid_next")
    assert "exceeded the daily call allocation limit" in str(exc_info.value)
    
    # Reset limit
    rate_limiter._local_daily[tenant_id] = []
