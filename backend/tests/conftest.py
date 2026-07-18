import os
os.environ["APP_ENV"] = "test"
import pytest
from opentelemetry import trace

# Seed environment variables BEFORE importing any application modules
os.environ["STRIPE_SECRET_KEY"] = "sk_live_test_key_visoora_verify"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_mock_webhook_secret_visoora"
os.environ["ANTHROPIC_API_KEY"] = "mock_anthropic_api_key_for_testing"

# Mock Supabase out completely
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
os.environ["SUPABASE_ANON_KEY"] = ""

@pytest.fixture(scope="session", autouse=True)
def shutdown_telemetry():
    yield
    # Cleanly shutdown OpenTelemetry tracing provider on session end to join exporter threads
    try:
        provider = trace.get_tracer_provider()
        if hasattr(provider, "shutdown"):
            provider.shutdown()
    except Exception:
        pass
