import pytest
import os
import json
import sys
import uuid
import time
from unittest.mock import patch
from fastapi.testclient import TestClient

# Add parent directory to sys.path to ensure modules resolve correctly
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from server.twilio_handler import app
from security.config import settings

client = TestClient(app)

def get_mock_jwt_payload(role: str = "agent", tenant_id: str = "test_tenant", email: str = "user@visoora.test") -> dict:
    return {
        "sub": str(uuid.uuid4()),
        "email": email,
        "role": role,
        "tenant_id": tenant_id,
        "exp": int(time.time()) + 3600,
        "aud": "authenticated"
    }

@pytest.fixture(autouse=True)
def setup_mock_data():
    # 1. Setup local onboarding progress config
    config_path = "recordings/local_onboarding_progress.json"
    original_config = None
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                original_config = json.load(f)
        except Exception:
            pass

    test_registry = {
        "test_tenant": {
            "isCompleted": True,
            "step1": {
                "companyName": "Simulator Test Org",
                "website": "https://simulatortest.com",
                "companyDescription": "Custom B2B Software Development & SaaS Advisory.",
                "valueProposition": "Run fully simulated B2B growth operations in a sandbox."
            },
            "step3": {
                "icpIndustries": ["technology", "software"],
                "icpRegions": ["north america"],
                "decisionMakerTitles": ["cto", "qa lead"],
                "avoidList": [],
                "competitors": ["SimulCorp"],
                "brandVoiceTone": "analytical and professional"
            }
        }
    }
    os.makedirs("recordings", exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(test_registry, f, indent=2)

    # 2. Setup local contacts registry for Opportunity Radar lookup
    contacts_path = "recordings/local_contacts_test_tenant.json"
    original_contacts = None
    if os.path.exists(contacts_path):
        try:
            with open(contacts_path, "r") as f:
                original_contacts = json.load(f)
        except Exception:
            pass

    test_contacts = [
        {"id": "c1", "company": "Simulatee Tech", "phone": "+12345"},
        {"id": "c2", "company": "Mocky Labs", "phone": "+67890"},
        {"id": "c3", "company": "Growth Partners", "phone": "+54321"}
    ]
    with open(contacts_path, "w") as f:
        json.dump(test_contacts, f, indent=2)

    yield

    # Restore original files
    if original_config is not None:
        with open(config_path, "w") as f:
            json.dump(original_config, f, indent=2)
    elif os.path.exists(config_path):
        try:
            os.remove(config_path)
        except Exception:
            pass

    if original_contacts is not None:
        with open(contacts_path, "w") as f:
            json.dump(original_contacts, f, indent=2)
    elif os.path.exists(contacts_path):
        try:
            os.remove(contacts_path)
        except Exception:
            pass


def get_mock_auth_headers():
    return {
        "Authorization": "Bearer valid_jwt_token"
    }


@patch("security.rbac.verify_supabase_jwt")
def test_simulate_strategy_endpoint(mock_verify):
    """Tests the outbound strategy simulator API."""
    mock_verify.return_value = get_mock_jwt_payload(role="agent", tenant_id="test_tenant")
    settings.app_env = "development"
    payload = {
        "segment": "Healthcare SaaS Startups",
        "region": "North America",
        "company_size": "50-200"
    }
    response = client.post(
        "/api/analytics/simulate-strategy",
        json=payload,
        headers=get_mock_auth_headers()
    )
    assert response.status_code == 200
    res_data = response.json()
    assert "market_size" in res_data
    assert "competition" in res_data
    assert "expected_acv" in res_data
    assert "expected_response_rate" in res_data
    assert "sales_cycle_days" in res_data
    assert "risk_score" in res_data
    assert "risk_analysis" in res_data


@patch("security.rbac.verify_supabase_jwt")
def test_opportunity_radar_endpoint(mock_verify):
    """Tests the daily opportunity trigger event radar API."""
    mock_verify.return_value = get_mock_jwt_payload(role="agent", tenant_id="test_tenant")
    settings.app_env = "development"
    response = client.get(
        "/api/analytics/opportunity-radar",
        headers=get_mock_auth_headers()
    )
    assert response.status_code == 200
    res_data = response.json()
    assert "events" in res_data
    assert len(res_data["events"]) > 0
    first_event = res_data["events"][0]
    assert "company" in first_event
    assert "trigger" in first_event
    assert "priority" in first_event


@patch("security.rbac.verify_supabase_jwt")
def test_business_map_endpoint(mock_verify):
    """Tests the cognitive AI business twin map retrieval API."""
    mock_verify.return_value = get_mock_jwt_payload(role="agent", tenant_id="test_tenant")
    settings.app_env = "development"
    response = client.get(
        "/api/analytics/business-map",
        headers=get_mock_auth_headers()
    )
    assert response.status_code == 200
    res_data = response.json()
    assert "agent_config" in res_data
    assert "icp_segments" in res_data["agent_config"]
    assert "buyer_personas" in res_data["agent_config"]
    assert "strengths" in res_data["agent_config"]
    assert "weaknesses" in res_data["agent_config"]
    
    # Verify value propagation from setup_mock_data config
    assert res_data["agent_config"]["company_description"] == "Custom B2B Software Development & SaaS Advisory."
    assert res_data["agent_config"]["value_proposition"] == "We build scaleable custom software, cloud apps, and modern API integrations."
