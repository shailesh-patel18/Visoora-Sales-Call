import pytest
import os
import json
import asyncio
from server.lead_scorer import calculate_and_save_lead_score
from crm.auto_advance import _load_local_json, _save_local_json

@pytest.fixture(autouse=True)
def setup_test_files():
    """Sets up local test registries for contact records and onboarding configs."""
    # 1. Setup local progress registry
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
                "companyName": "Test Tenant Corp",
                "website": "https://testtenant.com",
                "companyDescription": "We sell high-converting sales pipeline automation tools.",
                "valueProposition": "Increase booking rates by 40% with AI-driven voice SDRs."
            },
            "step3": {
                "icpIndustries": ["technology", "software", "healthcare"],
                "icpRegions": ["north america", "europe"],
                "decisionMakerTitles": ["ceo", "vp of sales", "founder"],
                "avoidList": ["competitor.com", "badspammer"],
                "competitors": ["crmgiant"],
                "brandVoiceTone": "Consultative and professional."
            }
        }
    }
    with open(config_path, "w") as f:
        json.dump(test_registry, f, indent=2)

    # 2. Setup local contacts registry
    contacts_path = "recordings/local_crm_contacts.json"
    original_contacts = None
    if os.path.exists(contacts_path):
        try:
            with open(contacts_path, "r") as f:
                original_contacts = json.load(f)
        except Exception:
            pass

    test_contacts = [
        {
            "id": "81a3d02b-8a8b-4c07-ba01-7fa7df8021c1",
            "tenant_id": "test_tenant",
            "full_name": "Avoid Person",
            "company_name": "Competitor LLC",
            "email": "spam@competitor.com",
            "title": "Software Engineer",
            "industry": "technology",
            "region": "north america",
            "tags": [],
            "custom_fields": {}
        },
        {
            "id": "92a3d02b-8a8b-4c07-ba01-7fa7df8021c2",
            "tenant_id": "test_tenant",
            "full_name": "Tony Stark",
            "company_name": "Stark Industries",
            "email": "tony@stark.com",
            "title": "VP of Sales",
            "industry": "technology",
            "region": "north america",
            "tags": [],
            "custom_fields": {}
        },
        {
            "id": "a3a3d02b-8a8b-4c07-ba01-7fa7df8021c3",
            "tenant_id": "test_tenant",
            "full_name": "John Doe",
            "company_name": "Unknown Co",
            "email": "john@unknown.com",
            "title": "Intern",
            "industry": "agriculture",
            "region": "asia",
            "tags": [],
            "custom_fields": {}
        }
    ]
    with open(contacts_path, "w") as f:
        json.dump(test_contacts, f, indent=2)

    yield

    # Restore original files
    if original_config is not None:
        with open(config_path, "w") as f:
            json.dump(original_config, f, indent=2)
    elif os.path.exists(config_path):
        os.remove(config_path)

    if original_contacts is not None:
        with open(contacts_path, "w") as f:
            json.dump(original_contacts, f, indent=2)
    elif os.path.exists(contacts_path):
        os.remove(contacts_path)

@pytest.mark.asyncio
async def test_lead_scoring_avoid_list():
    score, explanation, tags = await calculate_and_save_lead_score("81a3d02b-8a8b-4c07-ba01-7fa7df8021c1", "test_tenant")
    assert score == 0
    assert "matched avoid-list rule pattern" in explanation
    assert "objection-avoid-list" in tags

    # Verify write-back to local contacts registry
    contacts = _load_local_json("local_crm_contacts.json")
    contact = next(c for c in contacts if c["id"] == "81a3d02b-8a8b-4c07-ba01-7fa7df8021c1")
    assert contact["lead_score"] == 0
    assert "objection-avoid-list" in contact["tags"]

@pytest.mark.asyncio
async def test_lead_scoring_hot_lead():
    score, explanation, tags = await calculate_and_save_lead_score("92a3d02b-8a8b-4c07-ba01-7fa7df8021c2", "test_tenant")
    assert score >= 70
    assert "Decision maker title match" in explanation
    assert "ICP target industry match" in explanation
    assert "ICP target region match" in explanation

    contacts = _load_local_json("local_crm_contacts.json")
    contact = next(c for c in contacts if c["id"] == "92a3d02b-8a8b-4c07-ba01-7fa7df8021c2")
    assert contact["lead_score"] >= 70

@pytest.mark.asyncio
async def test_lead_scoring_cold_lead():
    score, explanation, tags = await calculate_and_save_lead_score("a3a3d02b-8a8b-4c07-ba01-7fa7df8021c3", "test_tenant")
    assert score == 20
    assert "cold-lead" in tags

    contacts = _load_local_json("local_crm_contacts.json")
    contact = next(c for c in contacts if c["id"] == "a3a3d02b-8a8b-4c07-ba01-7fa7df8021c3")
    assert contact["lead_score"] == 20
    assert "cold-lead" in contact["tags"]
