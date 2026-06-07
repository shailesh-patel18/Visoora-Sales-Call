import os
import sys

# ----------------------------------------------------
# 1. INITIAL SYSTEM ENVIRONMENT SEEDING
# ----------------------------------------------------
# Seed a live key to bypass sandbox fallback mode and run Stripe API calls
os.environ["STRIPE_SECRET_KEY"] = "sk_live_test_key_visoora_verify"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_mock_webhook_secret_visoora"

# Ensure the backend directory is in the import path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Bypass Supabase client database check by clearing it in storage manager
import server.storage_manager
server.storage_manager.supabase_client = None

# Bypass active Redis connection checks by clearing it in session registry
import server.session_registry
server.session_registry.redis_client = None

import pytest
import time
import json
import uuid
import datetime
from unittest.mock import patch, MagicMock, mock_open
from fastapi.testclient import TestClient

from server.twilio_handler import app
from security.config import settings
from billing.stripe_client import (
    create_stripe_customer,
    create_stripe_subscription,
    report_minute_usage,
    charge_one_time_topup,
    is_event_processed,
    LOCAL_EVENTS_FILE,
)
from billing.meter import (
    check_calling_limit,
    get_used_minutes,
    increment_used_minutes,
    get_tenant_billing_info,
    save_tenant_billing_info,
    LOCAL_USAGE_FILE,
    LOCAL_TENANTS_FILE,
)
from compliance.gate import verify_compliance_gate, ComplianceException

client = TestClient(app)

# Helper for secure header injection bypass
def get_admin_headers() -> dict:
    settings.system_api_keys.add("key_compliance_qa_testing")
    return {"X-API-Key": "key_compliance_qa_testing"}

# Helper to mock local billing files selectively
def mock_open_for_billing(tenants_data=None, usage_data=None, events_data=None):
    import builtins
    original_open = builtins.open
    
    tenants_json = json.dumps(tenants_data or [])
    usage_json = json.dumps(usage_data or [])
    events_json = json.dumps(events_data or [])
    
    def side_effect(file, *args, **kwargs):
        file_str = str(file)
        if "local_tenants.json" in file_str:
            return mock_open(read_data=tenants_json)()
        elif "local_billing_usage.json" in file_str:
            return mock_open(read_data=usage_json)()
        elif "local_billing_events.json" in file_str:
            return mock_open(read_data=events_json)()
        return original_open(file, *args, **kwargs)
        
    return patch("builtins.open", side_effect=side_effect)

# ====================================================
# TEST GROUP 1: STRIPE INTEGRATION WRAPPERS
# ====================================================
def test_stripe_customer_creation():
    """Asserts customer creation maps tenant_id and outputs stripe customer ID."""
    with patch("stripe.Customer.create") as mock_create:
        mock_create.return_value = MagicMock(id="cus_test_123")
        cus_id = create_stripe_customer("tenant_abc", "test@visoora.com", "Acme Corp")
        assert cus_id == "cus_test_123"
        mock_create.assert_called_once_with(
            email="test@visoora.com",
            name="Acme Corp",
            metadata={"tenant_id": "tenant_abc"}
        )

def test_stripe_subscription_creation():
    """Asserts subscription creates standard starter/pro items correctly."""
    with patch("stripe.Subscription.create") as mock_create:
        mock_create.return_value = MagicMock(id="sub_test_456")
        
        # Starter plan subscription
        sub_id = create_stripe_subscription("cus_test_123", "starter")
        assert sub_id == "sub_test_456"
        
        # Pro plan subscription
        sub_id = create_stripe_subscription("cus_test_123", "pro")
        assert sub_id == "sub_test_456"

def test_report_minute_usage():
    """Asserts calls increment metered Stripe subscription usages with ceilings of call minutes."""
    with patch("stripe.Subscription.retrieve") as mock_retrieve, \
         patch("stripe.StripeClient") as mock_client_class:
        
        mock_retrieve.return_value = {
            "items": {"data": [{"id": "si_test_888"}]}
        }
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.raw_request.return_value = MagicMock(id="ur_test_999")
        
        success = report_minute_usage("sub_test_456", 12.3)
        assert success is True
        mock_client.raw_request.assert_called_once()
        # CEIL of 12.3 is 13
        args, kwargs = mock_client.raw_request.call_args
        assert args[0] == "post"
        assert args[1] == "/v1/subscription_items/si_test_888/usage_records"
        assert kwargs["quantity"] == 13

def test_charge_one_time_topup():
    """Asserts instant card charging builds pending invoices and captures funds instantly."""
    with patch("stripe.InvoiceItem.create") as mock_item, \
         patch("stripe.Invoice.create") as mock_inv, \
         patch("stripe.Invoice.pay") as mock_pay:
        
        mock_item.return_value = MagicMock()
        mock_inv.return_value = MagicMock(id="in_test_111")
        mock_pay.return_value = MagicMock(paid=True, id="in_test_111")
        
        success = charge_one_time_topup("cus_test_123", amount_cents=2000)
        assert success is True
        mock_item.assert_called_once_with(
            customer="cus_test_123",
            amount=2000,
            currency="usd",
            description="Visoora Overage Call Minutes Top-up (120 Minutes)"
        )
        mock_inv.assert_called_once_with(customer="cus_test_123", auto_advance=True)
        mock_pay.assert_called_once_with("in_test_111")

# ====================================================
# TEST GROUP 2: USAGE ENFORCEMENT & COMPLIANCE GATE
# ====================================================
@pytest.mark.asyncio
async def test_compliance_gate_blocks_on_depleted_minutes():
    """Asserts calling gate raises ComplianceException when a tenant has 0 minutes remaining and auto-topup is disabled."""
    tenant_id = "tenant_depleted"
    
    # 0 included minutes, 0 purchased overage, 550 used minutes = depleted balance
    tenants_mock = [{
        "id": tenant_id,
        "plan": "starter",
        "is_calling_suspended": False,
        "auto_topup_enabled": False,
        "purchased_overage_minutes": 0.0,
    }]
    usage_mock = [{
        "tenant_id": tenant_id,
        "month": datetime.datetime.utcnow().strftime("%Y-%m"),
        "duration_minutes": 550.0, # Exceeds starter plan limit of 500
        "timestamp": datetime.datetime.utcnow().isoformat()
    }]
    
    with mock_open_for_billing(tenants_data=tenants_mock, usage_data=usage_mock):
        with pytest.raises(ComplianceException) as exc_info:
            await verify_compliance_gate("+15017122661", tenant_id, str(uuid.uuid4()))
            
        assert exc_info.value.status_code == 402
        assert "BILLING_SUSPENDED_NO_MINUTES" in exc_info.value.invalid_params[0]["reason"]

@pytest.mark.asyncio
async def test_auto_topup_credits_low_minutes_accounts():
    """Asserts check_calling_limit automatically triggers a $20 card topup on low minutes (<50) and credits 120 minutes."""
    tenant_id = "tenant_low_balance"
    
    tenants_mock = [{
        "id": tenant_id,
        "plan": "starter",
        "is_calling_suspended": False,
        "auto_topup_enabled": True, # Active opt-in
        "purchased_overage_minutes": 0.0,
        "stripe_customer_id": "cus_low_balance",
        "stripe_subscription_id": "sub_low_balance",
    }]
    # Used 520 mins out of 500 = depleted balance (remaining = -20.0 <= 0.0)
    usage_mock = [{
        "tenant_id": tenant_id,
        "month": datetime.datetime.utcnow().strftime("%Y-%m"),
        "duration_minutes": 520.0,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }]
    
    with mock_open_for_billing(tenants_data=tenants_mock, usage_data=usage_mock):
        with patch("billing.stripe_client.charge_one_time_topup", return_value=True) as mock_charge, \
             patch("billing.meter.save_tenant_billing_info", return_value=True) as mock_save:
            
            allowed = await check_calling_limit(tenant_id)
            assert allowed is True
            mock_charge.assert_called_once_with("cus_low_balance", amount_cents=2000)
            mock_save.assert_called_once_with(tenant_id, {"purchased_overage_minutes": 120.0})

# ====================================================
# TEST GROUP 3: BILLING WEBHOOK ROUTER & WEBHOOKS
# ====================================================
def test_get_usage_dashboard():
    """Asserts GET /billing/usage computes remaining limits and estimated billing correctly."""
    headers = get_admin_headers()
    tenant_id = "global_system_tenant" # Standard system tenant mapped from get_admin_headers X-API-Key
    
    tenants_mock = [{
        "id": tenant_id,
        "plan": "starter",
        "is_calling_suspended": False,
        "auto_topup_enabled": True,
        "purchased_overage_minutes": 120.0,
    }]
    usage_mock = [
        {"tenant_id": tenant_id, "month": datetime.datetime.utcnow().strftime("%Y-%m"), "duration_minutes": 100.0, "timestamp": datetime.datetime.utcnow().isoformat()},
        {"tenant_id": tenant_id, "month": datetime.datetime.utcnow().strftime("%Y-%m"), "duration_minutes": 250.0, "timestamp": datetime.datetime.utcnow().isoformat()}
    ]
    
    with mock_open_for_billing(tenants_data=tenants_mock, usage_data=usage_mock):
        response = client.get("/billing/usage", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "starter"
        assert data["used_minutes"] == 350.0 # 100 + 250
        # remaining = 500 (starter) + 120 (purchased) - 350 (used) = 270
        assert data["remaining_minutes"] == 270.0
        assert data["estimated_bill_usd"] == 99.00 # monthly fee, no overage (350 < 500)

def test_change_plan_endpoint():
    """Asserts POST /billing/change-plan updates plans and triggers proration modifications on Stripe."""
    headers = get_admin_headers()
    tenant_id = "global_system_tenant"
    
    tenants_mock = [{
        "id": tenant_id,
        "plan": "starter",
        "stripe_subscription_id": "sub_active_111",
    }]
    
    with mock_open_for_billing(tenants_data=tenants_mock):
        with patch("stripe.Subscription.retrieve") as mock_retrieve, \
             patch("stripe.Subscription.modify") as mock_modify, \
             patch("billing.router.save_tenant_billing_info", return_value=True) as mock_save:
            
            mock_retrieve.return_value = {
                "items": {"data": [MagicMock(id="si_item_222")]}
            }
            
            # Request upgrade to Pro plan
            response = client.post("/billing/change-plan", json={"plan": "pro"}, headers=headers)
            assert response.status_code == 200
            assert response.json()["plan"] == "pro"
            
            mock_modify.assert_called_once()
            args, kwargs = mock_modify.call_args
            assert args[0] == "sub_active_111"
            assert kwargs["proration_behavior"] == "always_invoice"
            assert kwargs["items"][0]["price"] == "price_pro_299_mo"

def test_auto_topup_toggle_endpoint():
    """Asserts POST /billing/toggle-auto-topup switches auto-topup opt-in flags."""
    headers = get_admin_headers()
    
    with patch("billing.router.save_tenant_billing_info", return_value=True) as mock_save:
        response = client.post("/billing/toggle-auto-topup", json={"enabled": True}, headers=headers)
        assert response.status_code == 200
        assert response.json()["auto_topup_enabled"] is True
        mock_save.assert_called_once_with("global_system_tenant", {"auto_topup_enabled": True})

# ====================================================
# TEST GROUP 4: WEBHOOK SIGNATURE & IDEMPOTENCY LOCKS
# ====================================================
def test_webhook_idempotency_ignores_duplicates():
    """Asserts is_event_processed blocks duplicate Stripe Webhook event IDs using local/redis registries."""
    event_id = "evt_stripe_test_123"
    
    # 1. First event processing -> should return False (not processed yet)
    with mock_open_for_billing(events_data=[]):
        processed = is_event_processed(event_id)
        assert processed is False

    # 2. Second event processing -> should return True (locked/duplicate)
    with mock_open_for_billing(events_data=[event_id]):
        processed = is_event_processed(event_id)
        assert processed is True

def test_webhook_suspends_on_payment_failed():
    """Asserts invoice.payment_failed Webhook sets is_calling_suspended=True instantly."""
    headers = {"Stripe-Signature": "mocked_sig"}
    
    payload = {
        "id": "evt_payment_failed_999",
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "customer": "cus_mocked_acme_tenant",
                "subscription": "sub_mocked_active"
            }
        }
    }
    
    with mock_open_for_billing(events_data=[]):
        with patch("stripe.Webhook.construct_event", return_value=payload), \
             patch("billing.router.save_tenant_billing_info", return_value=True) as mock_save:
            response = client.post("/billing/webhook", json=payload, headers=headers)
            assert response.status_code == 200
            # Should lock calling state
            mock_save.assert_any_call("acme_tenant", {"is_calling_suspended": True})
