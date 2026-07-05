import pytest
import os
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from server.twilio_handler import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def preserve_app_env():
    """Saves and restores settings.app_env to prevent leakage across tests."""
    from security.config import settings
    original_env = settings.app_env
    yield
    settings.app_env = original_env

@pytest.fixture(autouse=True)
def cleanup_local_auth_file():
    """Wipes active auth local JSON records to guarantee test isolation."""
    filepath = "recordings/local_auth_users.json"
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            pass
    yield
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            pass

def test_signup_and_login_flow():
    """Tests signing up and logging in using the mock authentication registry."""
    # 1. Signup a new user
    signup_payload = {
        "email": "agent@visoora.test",
        "password": "SecretPassword123",
        "full_name": "Test Agent",
        "company_name": "Visoora Test",
        "role": "agent"
    }
    
    # Force settings.app_env to development to ensure mock registry is active
    from security.config import settings
    settings.app_env = "development"
    
    response = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["user"]["email"] == "agent@visoora.test"
    assert res_data["user"]["role"] == "agent"
    assert res_data["user"]["tenant_id"] == "visoora.test"
    
    # 2. Duplicate signup should fail
    response = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 400
    
    # 3. Login with correct credentials
    login_payload = {
        "email": "agent@visoora.test",
        "password": "SecretPassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    login_data = response.json()
    assert "access_token" in login_data
    token = login_data["access_token"]
    assert login_data["user"]["role"] == "agent"
    assert login_data["user"]["tenant_id"] == "visoora.test"
    
    # 4. Login with invalid password
    invalid_login = {
        "email": "agent@visoora.test",
        "password": "WrongPassword"
    }
    response = client.post("/api/v1/auth/login", json=invalid_login)
    assert response.status_code == 401
    
    # 5. Access protected /me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    me_data = response.json()
    assert me_data["email"] == "agent@visoora.test"
    assert me_data["role"] == "agent"
    assert me_data["tenant_id"] == "visoora.test"
    
    # 6. Logout
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_expired_token():
    """Verifies that an expired JWT token is rejected with HTTP 401."""
    import jwt
    import datetime
    
    payload = {
        "sub": "user_123",
        "email": "user@test.com",
        "role": "agent",
        "tenant_id": "test_tenant",
        "aud": "authenticated",
        "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    }
    expired_token = jwt.encode(payload, "mock_secret_key_visoora_auth", algorithm="HS256")
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert "session expired" in response.json()["detail"].lower() or "signature has expired" in response.json()["detail"].lower()


def test_tenant_context_idor_protection():
    """Verifies that a user cannot query another tenant's data using X-Tenant-ID headers."""
    # Force settings.app_env to development to ensure mock registry is active
    from security.config import settings
    settings.app_env = "development"

    # 1. Signup and log in User 1 (tenant: tenant1.test)
    signup1 = {
        "email": "user1@tenant1.test",
        "password": "Password123",
        "full_name": "User One",
        "company_name": "Tenant One",
        "role": "agent"
    }
    client.post("/api/v1/auth/signup", json=signup1)
    res1 = client.post("/api/v1/auth/login", json={"email": "user1@tenant1.test", "password": "Password123"})
    token1 = res1.json()["access_token"]
    
    # 2. Signup User 2 (tenant: tenant2.test)
    signup2 = {
        "email": "user2@tenant2.test",
        "password": "Password123",
        "full_name": "User Two",
        "company_name": "Tenant Two",
        "role": "agent"
    }
    client.post("/api/v1/auth/signup", json=signup2)
    
    # 3. User 1 tries to call a tenant-scoped API endpoint with X-Tenant-ID: tenant2.test
    # This should be forbidden (403) due to tenant context mismatch.
    headers = {
        "Authorization": f"Bearer {token1}",
        "X-Tenant-ID": "tenant2.test"
    }
    response = client.get("/api/v1/sales-employee/agents", headers=headers)
    assert response.status_code == 403
    assert "tenant context mismatch" in response.json()["detail"].lower()


def test_production_environment_fallback_blocker():
    """Verifies that local mock registry fallbacks are blocked in production mode."""
    from security.config import settings
    # Set to production mode
    settings.app_env = "production"
    
    signup_payload = {
        "email": "agent@prod.test",
        "password": "Password123",
        "full_name": "Prod Agent",
        "company_name": "Prod Co",
        "role": "agent"
    }
    
    # Sign up should fail with 503
    response = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 503
    assert "offline" in response.json()["detail"].lower()
    
    # Login should fail with 503
    response = client.post("/api/v1/auth/login", json={"email": "agent@prod.test", "password": "Password123"})
    assert response.status_code == 503
