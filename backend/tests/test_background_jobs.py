import pytest
import os
import asyncio
from fastapi.testclient import TestClient
from server.twilio_handler import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def preserve_app_env():
    """Saves and restores settings.app_env to prevent leakage across tests."""
    from security.config import settings
    original_env = settings.app_env
    settings.app_env = "test"
    yield
    settings.app_env = original_env

@pytest.fixture(autouse=True)
def cleanup_local_jobs_file():
    """Wipes active jobs local JSON records to guarantee test isolation."""
    filepath = "recordings/local_background_jobs.json"
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

def test_background_job_lifecycle():
    # 1. Signup and login to get auth token
    signup_payload = {
        "email": "jobtest@visoora.test",
        "password": "SecretPassword123",
        "full_name": "Job Test User",
        "company_name": "Job Co",
        "role": "agent"
    }
    client.post("/api/v1/auth/signup", json=signup_payload)
    login_res = client.post("/api/v1/auth/login", json={"email": "jobtest@visoora.test", "password": "SecretPassword123"})
    token = login_res.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "visoora.test"
    }

    # 2. Queue a dummy job
    job_payload = {
        "job_type": "dummy",
        "payload": {"duration": 1}
    }
    response = client.post("/api/v1/jobs", json=job_payload, headers=headers)
    assert response.status_code == 201
    job_data = response.json()
    assert job_data["status"] == "queued"
    assert job_data["job_type"] == "dummy"
    job_id = job_data["id"]

    # 3. Poll job status - should be queued
    status_res = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "queued"

    # 4. Trigger worker processing directly
    from server.worker import process_next_job
    
    # Run the worker iteration once
    asyncio.run(process_next_job())

    # 5. Poll job status again - should be success
    status_res = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert status_res.status_code == 200
    job_result = status_res.json()
    assert job_result["status"] == "success"
    assert job_result["result"]["duration"] == 1
    assert "Dummy job completed" in job_result["result"]["message"]

    # 6. Verify cross-tenant access is blocked
    other_headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "other_tenant.test"
    }
    # Trying to post under other tenant should be forbidden
    response = client.post("/api/v1/jobs", json=job_payload, headers=other_headers)
    assert response.status_code == 403
