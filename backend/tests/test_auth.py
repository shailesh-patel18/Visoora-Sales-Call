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
