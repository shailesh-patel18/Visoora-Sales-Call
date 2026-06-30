import os
import pytest
from opentelemetry import trace

# Seed environment variables BEFORE importing any application modules
os.environ["STRIPE_SECRET_KEY"] = "sk_live_test_key_visoora_verify"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_mock_webhook_secret_visoora"

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
