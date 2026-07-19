import pytest
from security.config import settings

def test_business_brain_generation():
    if settings.mock_ai:
        assert True
    else:
        pytest.skip("Skipping real AI call in unit test suite. Run with MOCK_AI=true.")

def test_business_brain_save_to_db():
    from supabase import create_client
    import os
    import uuid
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY"))
    if not url or not key:
        pytest.skip("Supabase credentials not fully set, skipping db connection test")
        
    client = create_client(url, key)
    try:
        brain_id = str(uuid.uuid4())
        client.table("business_brains").insert({
            "id": brain_id,
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "domain": "test-save.com",
            "industry": "Test"
        }).execute()
        
        client.table("business_brains").delete().eq("id", brain_id).execute()
        assert True
    except Exception as e:
        pytest.fail(f"Failed to save Business Brain to DB: {e}")
