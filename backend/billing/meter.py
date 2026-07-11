import os
import json
import uuid
import asyncio
import datetime
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

import structlog
logger = structlog.get_logger("visoora_meter")

load_dotenv()

# Plan Threshold allocations
PLAN_INCLUDED_MINUTES = {
    "starter": 500.0,
    "pro": 2000.0,
    "enterprise": 999999.0
}

PLAN_OVERAGE_RATES = {
    "starter": 0.18,
    "pro": 0.15,
    "enterprise": 0.00
}

LOCAL_TENANTS_FILE = "recordings/local_tenants.json"
LOCAL_USAGE_FILE = "recordings/local_billing_usage.json"
local_db_lock = asyncio.Lock()

# Initial database files seeder
os.makedirs("recordings", exist_ok=True)
if not os.path.exists(LOCAL_USAGE_FILE):
    with open(LOCAL_USAGE_FILE, "w") as f:
        json.dump([], f)

# ----------------------------------------------------
# 1. DATABASE TENANT LOOKUP & WRITE
# ----------------------------------------------------
async def get_tenant_billing_info(tenant_id: str) -> Dict[str, Any]:
    """
    Reads tenant data from Supabase or the local thread-safe JSON database.
    Guarantees consistent default fields to prevent KeyErrors.
    """
    default_info = {
        "id": tenant_id,
        "name": "Acme Corp",
        "plan": "starter",
        "is_calling_suspended": False,
        "auto_topup_enabled": False,
        "purchased_overage_minutes": 0.0,
        "stripe_customer_id": f"cus_mocked_{tenant_id}",
        "stripe_subscription_id": f"sub_mocked_starter_{tenant_id[-8:]}",
        "twilio_phone": "+15017122661",
    }
    
    from server.storage_manager import supabase_admin_client as supabase_client
    if supabase_client:
        try:
            res = supabase_client.table("tenants").select("*").eq("id", tenant_id).execute()
            if res.data:
                # Merge with defaults to ensure typing safety
                return {**default_info, **res.data[0]}
        except Exception as e:
            logger.error("supabase_tenant_read_failed", tenant_id=tenant_id, error=str(e))

    # Local JSON fallback lookup
    async with local_db_lock:
        try:
            with open(LOCAL_TENANTS_FILE, "r") as f:
                tenants = json.load(f)
            for t in tenants:
                if t.get("id") == tenant_id:
                    return {**default_info, **t}
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error("local_tenants_read_failed", error=str(e))

    # Pre-seed if missing
    return default_info

async def save_tenant_billing_info(tenant_id: str, updates: Dict[str, Any]) -> bool:
    """
    Saves billing update parameters to Postgres Supabase or the local JSON registry.
    """
    logger.info("save_tenant_billing_info_start", tenant_id=tenant_id, updates=updates)
    
    from server.storage_manager import supabase_admin_client as supabase_client
    if supabase_client:
        try:
            supabase_client.table("tenants").update(updates).eq("id", tenant_id).execute()
            return True
        except Exception as e:
            logger.error("supabase_tenant_write_failed", tenant_id=tenant_id, error=str(e))

    # Local JSON fallback update
    async with local_db_lock:
        try:
            tenants = []
            if os.path.exists(LOCAL_TENANTS_FILE):
                with open(LOCAL_TENANTS_FILE, "r") as f:
                    tenants = json.load(f)
            
            found = False
            for t in tenants:
                if t.get("id") == tenant_id:
                    for k, v in updates.items():
                        t[k] = v
                    found = True
                    break
            
            if not found:
                # Seed a new one
                new_tenant = {
                    "id": tenant_id,
                    "name": "Acme Corp",
                    "twilio_phone": "+15017122661",
                    **updates
                }
                tenants.append(new_tenant)
                
            with open(LOCAL_TENANTS_FILE, "w") as f:
                json.dump(tenants, f, indent=2)
            return True
        except Exception as e:
            logger.error("local_tenants_write_failed", error=str(e))
            return False

# ----------------------------------------------------
# 2. REAL-TIME USAGE ACCUMULATOR & GETTERS
# ----------------------------------------------------
def get_used_minutes(tenant_id: str, month_str: Optional[str] = None) -> float:
    """
    Checks active monthly call minutes in Redis, cascading to local JSON audits on connection faults.
    """
    if not month_str:
        month_str = datetime.datetime.utcnow().strftime("%Y-%m")

    from server.session_registry import redis_client
    # 1. Redis high-speed query
    if redis_client:
        try:
            counter_key = f"visoora:billing:used_minutes:{tenant_id}:{month_str}"
            val = redis_client.get(counter_key)
            if val is not None:
                return float(val)
        except Exception as e:
            logger.error("redis_used_minutes_failed", tenant_id=tenant_id, error=str(e))

    # 2. Local Fallback query
    try:
        with open(LOCAL_USAGE_FILE, "r") as f:
            records = json.load(f)
        
        total = 0.0
        for r in records:
            if r.get("tenant_id") == tenant_id and r.get("month") == month_str:
                total += r.get("duration_minutes", 0.0)
        return total
    except Exception as e:
        logger.error("local_usage_read_failed", error=str(e))
        return 0.0

async def increment_used_minutes(tenant_id: str, minutes_to_add: float):
    """
    Increments monthly call usage counters in Redis, registers audit trails,
    reports metered usages to Stripe subscription items, and checks compliance alert triggers.
    """
    month_str = datetime.datetime.utcnow().strftime("%Y-%m")
    logger.info("increment_used_minutes_start", tenant_id=tenant_id, minutes=minutes_to_add)

    # 1. Update Redis Cache Counter
    from server.session_registry import redis_client
    if redis_client:
        try:
            counter_key = f"visoora:billing:used_minutes:{tenant_id}:{month_str}"
            redis_client.incrbyfloat(counter_key, minutes_to_add)
            # Set key expiry to 45 days so it spans past the current month cleanly
            redis_client.expire(counter_key, 3888000)
        except Exception as e:
            logger.error("redis_usage_increment_failed", tenant_id=tenant_id, error=str(e))

    # 2. Insert into Local JSON Audit logs (Postgres audit fallback)
    try:
        with open(LOCAL_USAGE_FILE, "r") as f:
            records = json.load(f)
            
        records.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "month": month_str,
            "duration_minutes": minutes_to_add,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        
        with open(LOCAL_USAGE_FILE, "w") as f:
            json.dump(records, f, indent=2)
    except Exception as e:
        logger.error("local_usage_write_failed", error=str(e))

    # 3. Report Meted usage directly to Stripe API
    tenant_info = await get_tenant_billing_info(tenant_id)
    sub_id = tenant_info.get("stripe_subscription_id")
    if sub_id:
        from billing.stripe_client import report_minute_usage
        report_minute_usage(sub_id, minutes_to_add)

    # 4. Trigger threshold alert validations
    await _check_usage_alerts(tenant_id, tenant_info, month_str)
    
    # 5. Check hourly spike abuse rules
    await _check_usage_spike(tenant_id, minutes_to_add)


# ----------------------------------------------------
# 3. LIMIT ENFORCER & COMPLIANCE WEBHOOK BLOCKED
# ----------------------------------------------------
async def check_calling_limit(tenant_id: str) -> bool:
    """
    Zero-trust boundary check prior to triggering outboundTwilio PSTN calls.
    Returns: True if call is approved to connect, False if blocked.
    """
    tenant_info = await get_tenant_billing_info(tenant_id)
    
    # Block immediately if manual suspension flag is checked
    if tenant_info.get("is_calling_suspended", False):
        logger.warn("calling_blocked_manual_suspension", tenant_id=tenant_id)
        return False

    plan = tenant_info.get("plan", "starter")
    plan_limit = PLAN_INCLUDED_MINUTES.get(plan, 500.0)
    overage_allowed = tenant_info.get("purchased_overage_minutes", 0.0)
    used_minutes = get_used_minutes(tenant_id)

    remaining_minutes = plan_limit + overage_allowed - used_minutes
    logger.info("checking_limits_meter", tenant_id=tenant_id, plan=plan, remaining=remaining_minutes)

    if remaining_minutes <= 0.0:
        # Check if Tenant has opted-in for auto balance Topup refilling
        if tenant_info.get("auto_topup_enabled", False):
            logger.info("auto_topup_triggered", tenant_id=tenant_id)
            
            # Charge $20 standard card charge for 120 additional overage minutes
            from billing.stripe_client import charge_one_time_topup
            cus_id = tenant_info.get("stripe_customer_id")
            
            success = charge_one_time_topup(cus_id, amount_cents=2000)
            if success:
                new_overage = overage_allowed + 120.0
                await save_tenant_billing_info(tenant_id, {
                    "purchased_overage_minutes": new_overage
                })
                logger.info("auto_topup_credited_success", tenant_id=tenant_id, new_overage=new_overage)
                return True
            else:
                # Topup failed, suspend account
                await save_tenant_billing_info(tenant_id, {
                    "is_calling_suspended": True
                })
                logger.error("auto_topup_charge_failed_suspending", tenant_id=tenant_id)
                await _send_suspension_alert_email(tenant_info)
                return False
        else:
            logger.warn("calling_blocked_depleted_minutes", tenant_id=tenant_id)
            return False

    return True

# ----------------------------------------------------
# 4. NOTIFICATION & ANOMALY ENGINES (Resend & Slack Webhooks)
# ----------------------------------------------------
async def _check_usage_alerts(tenant_id: str, tenant_info: dict, month_str: str):
    """
    Monitors consumed minutes ratios and dispatches alert emails when crossing 75% or 95%.
    """
    plan = tenant_info.get("plan", "starter")
    limit = PLAN_INCLUDED_MINUTES.get(plan, 500.0)
    used = get_used_minutes(tenant_id, month_str)
    ratio = used / limit if limit > 0 else 0.0

    # Ensure warning events only fire once per billing boundary by saving alert state
    alert_75_fired = tenant_info.get("alert_75_fired", False)
    alert_95_fired = tenant_info.get("alert_95_fired", False)

    if ratio >= 0.95 and not alert_95_fired:
        logger.warn("usage_warning_95", tenant_id=tenant_id, ratio=ratio)
        await save_tenant_billing_info(tenant_id, {"alert_95_fired": True})
        await _send_limit_email(tenant_info, "95%", used, limit)
    elif ratio >= 0.75 and not alert_75_fired and ratio < 0.95:
        logger.info("usage_warning_75", tenant_id=tenant_id, ratio=ratio)
        await save_tenant_billing_info(tenant_id, {"alert_75_fired": True})
        await _send_limit_email(tenant_info, "75%", used, limit)

async def _check_usage_spike(tenant_id: str, minutes_added: float):
    """
    Tracks call metrics over sliding 1-hour window.
    Triggers Slack alert to ops team if usage exceeds 3x daily average (traffic anomaly).
    """
    # Sum used minutes in current month
    month_str = datetime.datetime.utcnow().strftime("%Y-%m")
    used_total = get_used_minutes(tenant_id, month_str)
    
    current_day = datetime.datetime.utcnow().day
    daily_average = used_total / max(current_day, 1)

    # Sum usage in last 1 hour
    try:
        with open(LOCAL_USAGE_FILE, "r") as f:
            records = json.load(f)
            
        one_hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        hourly_total = 0.0
        
        for r in records:
            if r.get("tenant_id") == tenant_id:
                dt = datetime.datetime.fromisoformat(r.get("timestamp"))
                if dt > one_hour_ago:
                    hourly_total += r.get("duration_minutes", 0.0)
        
        # Trigger alert spike threshold check (minimum baseline of 10 minutes required to avoid false positives)
        if hourly_total > 10.0 and hourly_total > (3.0 * daily_average):
            logger.warn("usage_spike_anomaly_detected", tenant_id=tenant_id, hourly_total=hourly_total, daily_avg=daily_average)
            await _send_slack_ops_alert(tenant_id, hourly_total, daily_average)
    except Exception as e:
        logger.error("usage_spike_check_failed", error=str(e))

# Mock Integrations
async def _send_limit_email(tenant_info: dict, threshold: str, used: float, limit: float):
    logger.info("email_notification_resend", to=tenant_info.get("name"), subject=f"Visoora Usage Alert: {threshold} consumed")

async def _send_suspension_alert_email(tenant_info: dict):
    logger.info("email_notification_resend", to=tenant_info.get("name"), subject="Visoora Calling Suspended: Depleted Balance")

async def _send_slack_ops_alert(tenant_id: str, hourly: float, avg: float):
    logger.warn("slack_alert_ops_channel", channel="#ops-alerts", message=f"Traffic Spike Anomaly: Tenant {tenant_id} consumed {hourly:.1f} minutes in 1hr (30-day daily avg: {avg:.1f} min)")
