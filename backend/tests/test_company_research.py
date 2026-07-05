import pytest
import os
import json
import asyncio
from unittest.mock import AsyncMock, patch
from server.company_research import check_robots_txt_allows, run_company_research
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
                "companyName": "Test Tenant Corp",
                "website": "https://testtenant.com",
                "companyDescription": "We sell high-converting sales pipeline automation tools.",
                "valueProposition": "Increase booking rates by 40% with AI-driven voice SDRs."
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
            "id": "71a3d02b-8a8b-4c07-ba01-7fa7df8021c1",
            "tenant_id": "test_tenant",
            "full_name": "Sarah Connor",
            "company_name": "Cyberdyne Systems",
            "email": "sarah@cyberdyne.com",
            "title": "Director of Operations",
            "industry": "technology",
            "region": "north america",
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
async def test_robots_txt_allows_disallowed():
    # Setup mock robots.txt text disallowing all bots
    robots_content = "User-agent: *\nDisallow: /"
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = robots_content
        mock_get.return_value = mock_response
        
        allowed = await check_robots_txt_allows("https://cyberdyne.com/about")
        assert allowed is False


@pytest.mark.asyncio
async def test_robots_txt_allows_allowed():
    # Setup mock robots.txt allowing bots
    robots_content = "User-agent: *\nDisallow: /private\nAllow: /"
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = robots_content
        mock_get.return_value = mock_response
        
        allowed = await check_robots_txt_allows("https://cyberdyne.com/about")
        assert allowed is True


@pytest.mark.asyncio
async def test_company_research_respects_robots_txt_block():
    robots_content = "User-agent: *\nDisallow: /"
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_robots_res = AsyncMock()
        mock_robots_res.status_code = 200
        mock_robots_res.text = robots_content
        
        mock_get.return_value = mock_robots_res
        
        # Run research
        result = await run_company_research("71a3d02b-8a8b-4c07-ba01-7fa7df8021c1", "test_tenant")
        
        # Verify that scraping was disallowed in metadata facts
        metadata = result.get("metadata_facts") or []
        assert any("disallowed by robots.txt" in item for item in metadata)
        
        # Verify results saved to local json
        contacts = _load_local_json("local_crm_contacts.json")
        contact = next(c for c in contacts if c["id"] == "71a3d02b-8a8b-4c07-ba01-7fa7df8021c1")
        assert "research_data" in contact["custom_fields"]
        assert len(contact["custom_fields"]["research_data"]["sourced_facts"]) > 0
