import pytest
import os
import json
import asyncio
from server.email_generator import run_email_generation
from crm.auto_advance import _load_local_json, _save_local_json

@pytest.fixture(autouse=True)
def setup_test_files():
    """Sets up local test registries for contact records and onboarding configs."""
    # Setup local progress registry
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
                "companyName": "Acme Sales automation LLC",
                "website": "https://acmesales.com",
                "companyDescription": "We sell automated SDR voice calls for B2B tech.",
                "valueProposition": "Automate outbound prospecting and book 3x more demos."
            }
        }
    }
    with open(config_path, "w") as f:
        json.dump(test_registry, f, indent=2)

    # Setup local contacts registry
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
            "id": "61a3d02b-8a8b-4c07-ba01-7fa7df8021c1",
            "tenant_id": "test_tenant",
            "full_name": "Tony Stark",
            "company_name": "Stark Industries",
            "email": "tony@stark.com",
            "title": "CEO",
            "industry": "technology",
            "region": "north america",
            "tags": [],
            "custom_fields": {
                "research_data": {
                    "sourced_facts": [
                        {"fact": "Headquarters in Los Angeles, California", "source": "Scraped site", "url": "https://stark.com"}
                    ]
                }
            }
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
async def test_email_generation_fallback():
    # Bypasses LLM correctly and utilizes baseline templates preserving client/brand details
    email = await run_email_generation("61a3d02b-8a8b-4c07-ba01-7fa7df8021c1", "test_tenant")
    assert "Acme Sales automation LLC" in email["body"]
    assert "Tony Stark" in email["body"]
    assert email["status"] == "review"

    # Verify saved in local contacts custom fields
    contacts = _load_local_json("local_crm_contacts.json")
    contact = next(c for c in contacts if c["id"] == "61a3d02b-8a8b-4c07-ba01-7fa7df8021c1")
    assert "outreach_email" in contact["custom_fields"]
    assert contact["custom_fields"]["outreach_email"]["status"] == "review"
    assert "Acme Sales automation LLC" in contact["custom_fields"]["outreach_email"]["body"]
