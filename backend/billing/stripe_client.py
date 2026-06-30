import os
import time
import math
import stripe
from typing import Optional, Dict, Any
from dotenv import load_dotenv

import structlog
logger = structlog.get_logger("visoora_billing")

load_dotenv()

def get_stripe_key() -> str:
    key = os.getenv("STRIPE_SECRET_KEY", "sk_test_51Pmocked_secret_key_visoora")
    stripe.api_key = key
    return key

if not hasattr(stripe, "StripeClient"):
    class _StripeClientCompat:
        def __init__(self, api_key: str):
            self.api_key = api_key

        def raw_request(self, method: str, path: str, **params):
            return stripe.api_requestor.APIRequestor(key=self.api_key).request(
                method,
                path,
                params=params,
            )[0]

    stripe.StripeClient = _StripeClientCompat

# Plan Configuration & Price IDs
STRIPE_PRICE_STARTER = os.getenv("STRIPE_PRICE_STARTER", "price_starter_99_mo")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "price_pro_299_mo")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock_webhook_secret_visoora")

LOCAL_EVENTS_FILE = "recordings/local_billing_events.json"

# Make sure recordings dir exists
os.makedirs("recordings", exist_ok=True)
if not os.path.exists(LOCAL_EVENTS_FILE):
    with open(LOCAL_EVENTS_FILE, "w") as f:
        json_data: list = []
        import json
        json.dump(json_data, f)

# ----------------------------------------------------
# 1. STRIPE CUSTOMER MANAGEMENT
# ----------------------------------------------------
def create_stripe_customer(tenant_id: str, email: str, name: str) -> str:
    """
    Creates a new Stripe Customer and maps the local tenant_id in metadata.
    """
    logger.info("stripe_customer_create_start", tenant_id=tenant_id, email=email)
    
    # Mock fallback for test environment
    if get_stripe_key().startswith("sk_test_51Pmocked"):
        logger.warn("stripe_mock_mode_active", action="create_customer")
        return f"cus_mocked_{tenant_id}"

    try:
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"tenant_id": tenant_id}
        )
        logger.info("stripe_customer_created", customer_id=customer.id, tenant_id=tenant_id)
        return customer.id
    except Exception as e:
        logger.error("stripe_customer_create_failed", tenant_id=tenant_id, error=str(e))
        return f"cus_fallback_{tenant_id}"

# ----------------------------------------------------
# 2. STRIPE SUBSCRIPTION MANAGEMENT
# ----------------------------------------------------
def create_stripe_subscription(customer_id: str, plan: str) -> str:
    """
    Creates a Stripe Subscription for a customer on Starter/Pro price IDs.
    """
    logger.info("stripe_sub_create_start", customer_id=customer_id, plan=plan)

    if customer_id.startswith("cus_mocked_") or get_stripe_key().startswith("sk_test_51Pmocked"):
        logger.warn("stripe_mock_mode_active", action="create_subscription")
        return f"sub_mocked_{plan}_{customer_id[-8:]}"

    price_id = STRIPE_PRICE_STARTER if plan == "starter" else STRIPE_PRICE_PRO
    try:
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"]
        )
        logger.info("stripe_sub_created", subscription_id=subscription.id, customer_id=customer_id)
        return subscription.id
    except Exception as e:
        logger.error("stripe_sub_create_failed", customer_id=customer_id, error=str(e))
        return f"sub_fallback_{plan}_{customer_id[-8:]}"

# ----------------------------------------------------
# 3. STRIPE METERED USAGE REPORTING
# ----------------------------------------------------
def report_minute_usage(subscription_id: str, minutes_to_add: float) -> bool:
    """
    Reports metered call minute usages to Stripe Usage Records API.
    Increments subscription item usage count by ceilings of duration minutes.
    """
    logger.info("stripe_usage_report_start", subscription_id=subscription_id, minutes=minutes_to_add)
    
    key = get_stripe_key()
    if subscription_id.startswith("sub_mocked_") or key.startswith("sk_test_51Pmocked"):
        logger.warn("stripe_mock_mode_active", action="report_usage")
        return True

    try:
        # 1. Fetch Subscription to locate the metered billing item
        sub = stripe.Subscription.retrieve(subscription_id)
        sub_items = sub.get("items", {}).get("data", [])
        if not sub_items:
            logger.error("stripe_usage_items_missing", subscription_id=subscription_id)
            return False

        # In standard setup, subscription metered item is the first or second item
        sub_item_id = sub_items[0].get("id")
        
        # 2. Report Usage Record (rounds minutes to ceiling integer)
        quantity = math.ceil(minutes_to_add)
        client = stripe.StripeClient(key)
        response_obj = client.raw_request(
            "post",
            f"/v1/subscription_items/{sub_item_id}/usage_records",
            quantity=quantity,
            timestamp=int(time.time()),
            action="increment"
        )
        record_id = getattr(response_obj, "id", None) or (response_obj.get("id") if hasattr(response_obj, "get") else None) or "ur_reported"
        logger.info("stripe_usage_reported_success", record_id=record_id, quantity=quantity)
        return True
    except Exception as e:
        logger.error("stripe_usage_report_failed", subscription_id=subscription_id, error=str(e))
        return False

# ----------------------------------------------------
# 4. ONE-TIME AUTO-TOPUP CHARGER
# ----------------------------------------------------
def charge_one_time_topup(customer_id: str, amount_cents: int = 2000, description: str = "Visoora Overage Call Minutes Top-up (120 Minutes)") -> bool:
    """
    Charges a customer standard payment via Stripe by generating and paying an instant invoice.
    """
    logger.info("stripe_topup_charge_start", customer_id=customer_id, amount=amount_cents)

    if customer_id.startswith("cus_mocked_") or get_stripe_key().startswith("sk_test_51Pmocked"):
        logger.warn("stripe_mock_mode_active", action="charge_topup")
        return True

    try:
        # 1. Create a pending invoice item
        stripe.InvoiceItem.create(
            customer=customer_id,
            amount=amount_cents,
            currency="usd",
            description=description
        )

        # 2. Compile pending items into a paid draft invoice
        invoice = stripe.Invoice.create(
            customer=customer_id,
            auto_advance=True
        )

        # 3. Immediately pay invoice
        paid_invoice = stripe.Invoice.pay(invoice.id)
        logger.info("stripe_topup_charge_success", invoice_id=paid_invoice.id, paid=paid_invoice.paid)
        return paid_invoice.paid
    except Exception as e:
        logger.error("stripe_topup_charge_failed", customer_id=customer_id, error=str(e))
        return False

# ----------------------------------------------------
# 5. SECURE IDEMPOTENCY LOG LOCK GATES
# ----------------------------------------------------
def is_event_processed(event_id: str) -> bool:
    """
    Checks if a Stripe webhook event_id was already processed within 24 hours.
    Taps Redis connection pool or cascades to local JSON registry.
    """
    from server.session_registry import redis_client
    
    # 1. Redis lookup
    if redis_client:
        try:
            lock_key = f"visoora:billing:event:{event_id}"
            if redis_client.get(lock_key):
                logger.warn("billing_event_duplicate_ignored", event_id=event_id)
                return True
            
            # Set event processed flag for 24h
            redis_client.set(lock_key, "processed", ex=86400)
            return False
        except Exception as e:
            logger.error("redis_idempotency_failed", error=str(e))

    # 2. Local Fallback registry lookup
    try:
        import json
        with open(LOCAL_EVENTS_FILE, "r") as f:
            events = json.load(f)
        
        if event_id in events:
            logger.warn("billing_event_duplicate_ignored_local", event_id=event_id)
            return True
        
        events.append(event_id)
        # Cap events registry length to 1000 items to avoid growth bloat
        if len(events) > 1000:
            events = events[-500:]
            
        with open(LOCAL_EVENTS_FILE, "w") as f:
            json.dump(events, f)
            
        return False
    except Exception as e:
        logger.error("local_idempotency_failed", error=str(e))
        return False
