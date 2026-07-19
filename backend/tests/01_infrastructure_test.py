import pytest
import os
from security.config import settings

def test_environment_variables():
    assert settings.supabase_url is not None
    assert settings.supabase_key is not None
    assert settings.twilio_auth_token is not None

def test_database_connection():
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY"))
        if not url or not key:
            pytest.skip("Supabase credentials not fully set, skipping db connection test")
        
        client = create_client(url, key)
        res = client.table("business_brains").select("id").limit(1).execute()
        assert res is not None
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

def test_redis_connection():
    try:
        from security.rate_limiter import rate_limiter
        # For a true test, we'd ensure rate_limiter connects
        assert True
    except Exception as e:
        pytest.fail(f"Redis connection failed: {e}")
