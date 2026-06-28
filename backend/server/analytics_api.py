"""
analytics_api.py — Dashboard analytics endpoints.

Fixes applied:
- Replaced broken `security.auth.verify_jwt` import with correct `security.rbac.get_current_user`
- Replaced broken `server.session_registry.redis_client` module-level import with lazy import
  (redis_client is a module-level variable that may not be initialized at import time)
- Added local-JSON fallback for /dashboard (M2.1b): when Supabase is offline, compute
  metrics from recordings/local_call_logs.json instead of raising HTTP 500
- Registered by `app.include_router(analytics_router, prefix="/api")` in twilio_handler.py
"""
import os
import json
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from security.rbac import get_current_user, UserPrincipal
from server.storage_manager import supabase_client
from security.config import settings

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

LOCAL_CALL_LOGS_PATH = "recordings/local_call_logs.json"


def _get_redis_client():
    """Lazy import of redis_client to avoid import-time failures when Redis is offline."""
    try:
        from server.session_registry import redis_client
        return redis_client
    except Exception:
        return None


def _aggregate_from_local_logs(tenant_id: str) -> Dict[str, Any]:
    """
    Compute dashboard metrics from local_call_logs.json when Supabase is offline.
    This mirrors the Supabase query in get_dashboard_metrics().
    """
    logs = []
    if os.path.exists(LOCAL_CALL_LOGS_PATH):
        try:
            with open(LOCAL_CALL_LOGS_PATH, "r") as f:
                all_logs = json.load(f)
            # Apply tenant isolation on the local file
            logs = [log for log in all_logs if log.get("tenant_id") == tenant_id]
        except Exception:
            logs = []

    total_calls = len(logs)
    total_duration = sum(log.get("duration_seconds", 0) for log in logs)
    success_calls = sum(
        1 for log in logs
        if log.get("final_state") in {"SUCCESS_COMPLETE", "BOOKING", "QUALIFICATION"}
    )
    success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0

    return {
        "total_calls": total_calls,
        "total_duration_seconds": total_duration,
        "success_rate_percent": round(success_rate, 2),
        "success_calls": success_calls,
        "source": "local_fallback"
    }


@analytics_router.get("/dashboard")
async def get_dashboard_metrics(user: UserPrincipal = Depends(get_current_user)):
    """
    Returns aggregate call metrics for the authenticated tenant's dashboard.
    Falls back to local_call_logs.json when Supabase is offline (M2.1b).
    Results are cached in Redis for 5 minutes when Redis is available.
    """
    tenant_id = user.tenant_id
    cache_key = f"analytics:dashboard:{tenant_id}"

    redis_client = _get_redis_client()
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # Redis failure — proceed to DB/local fallback

    if not supabase_client:
        if settings.app_env not in ("development", "test"):
            raise HTTPException(status_code=500, detail="Database connection offline.")
        # M2.1b: Compute metrics from local JSON instead of raising 500
        payload = _aggregate_from_local_logs(tenant_id)
        return payload

    # Live Supabase path
    try:
        logs_res = (
            supabase_client.table("call_logs")
            .select("duration_seconds, final_state")
            .eq("tenant_id", tenant_id)
            .execute()
        )
        logs = logs_res.data or []
    except Exception as e:
        if settings.app_env not in ("development", "test"):
            raise HTTPException(status_code=500, detail="Failed to retrieve dashboard metrics.")
        # Supabase configured but query failed — fall back to local
        payload = _aggregate_from_local_logs(tenant_id)
        return payload

    total_calls = len(logs)
    total_duration = sum(log.get("duration_seconds", 0) for log in logs)
    success_calls = sum(
        1 for log in logs
        if log.get("final_state") in {"SUCCESS_COMPLETE", "BOOKING", "QUALIFICATION"}
    )
    success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0

    payload = {
        "total_calls": total_calls,
        "total_duration_seconds": total_duration,
        "success_rate_percent": round(success_rate, 2),
        "success_calls": success_calls,
        "source": "supabase"
    }

    if redis_client:
        try:
            redis_client.set(cache_key, json.dumps(payload), ex=300)
        except Exception:
            pass

    return payload


@analytics_router.get("/funnel")
async def get_funnel_metrics(user: UserPrincipal = Depends(get_current_user)):
    """Returns deal funnel stage distribution for the authenticated tenant."""
    tenant_id = user.tenant_id
    cache_key = f"analytics:funnel:{tenant_id}"

    redis_client = _get_redis_client()
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    if not supabase_client:
        if settings.app_env not in ("development", "test"):
            raise HTTPException(status_code=500, detail="Database connection offline.")
        return {"funnel": [], "source": "local_fallback"}

    try:
        deals_res = supabase_client.table("deals").select("stage_id").eq("tenant_id", tenant_id).execute()
        stages_res = (
            supabase_client.table("pipeline_stages")
            .select("id, name, position")
            .eq("tenant_id", tenant_id)
            .order("position")
            .execute()
        )
    except Exception:
        if settings.app_env not in ("development", "test"):
            raise HTTPException(status_code=500, detail="Failed to retrieve funnel metrics.")
        return {"funnel": [], "source": "local_fallback"}

    deals = deals_res.data or []
    stages = stages_res.data or []

    stage_counts = {stage["id"]: {"name": stage["name"], "count": 0} for stage in stages}
    for deal in deals:
        sid = deal.get("stage_id")
        if sid in stage_counts:
            stage_counts[sid]["count"] += 1

    payload = {"funnel": list(stage_counts.values()), "source": "supabase"}

    if redis_client:
        try:
            redis_client.set(cache_key, json.dumps(payload), ex=300)
        except Exception:
            pass

    return payload


@analytics_router.get("/agents")
async def get_agent_metrics(user: UserPrincipal = Depends(get_current_user)):
    """Returns LLM latency percentile metrics for the admin dashboard."""
    cache_key = "analytics:agents:latency"

    redis_client = _get_redis_client()
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    # In future this would query Prometheus or a telemetry DB.
    # For now, the LatencyEnforcer in llm_guard.py tracks per-call latencies
    # but doesn't yet expose an aggregate API. Return structural zeroes.
    payload = {
        "p50_latency_ms": 0,
        "p90_latency_ms": 0,
        "p99_latency_ms": 0,
        "active_fallback_rate": "0.0%",
        "source": "not_yet_instrumented"
    }

    if redis_client:
        try:
            redis_client.set(cache_key, json.dumps(payload), ex=300)
        except Exception:
            pass

    return payload


# ====================================================
# CALL HISTORY LIST  —  GET /api/analytics/calls
# ====================================================
@analytics_router.get("/calls")
async def list_call_logs(
    user: UserPrincipal = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    search: str = "",
):
    """
    Returns a paginated list of call log records for the authenticated tenant.
    Supports optional `search` query param to filter by phone number or final state.
    Falls back to local_call_logs.json when Supabase is offline.

    Added as part of Rec 4 (executive audit): wires the Call History page
    to real backend data instead of deterministic mock data.
    """
    tenant_id = user.tenant_id

    # ── Local JSON fallback (no Supabase) ──────────────────────────────────
    if not supabase_client:
        if settings.app_env not in ("development", "test"):
            raise HTTPException(status_code=500, detail="Database connection offline.")
        logs = []
        if os.path.exists(LOCAL_CALL_LOGS_PATH):
            try:
                with open(LOCAL_CALL_LOGS_PATH, "r") as f:
                    all_logs = json.load(f)
                # Tenant isolation on local file
                logs = [lg for lg in all_logs if lg.get("tenant_id") == tenant_id]
            except Exception:
                logs = []

        if search:
            search_lower = search.lower()
            logs = [
                lg for lg in logs
                if search_lower in lg.get("phone_number", "").lower()
                or search_lower in lg.get("final_state", "").lower()
            ]

        # Sort newest first, paginate
        logs = sorted(logs, key=lambda x: x.get("created_at", ""), reverse=True)
        page = logs[offset : offset + limit]
        return {"calls": page, "total": len(logs), "source": "local_fallback"}

    # ── Supabase live path ──────────────────────────────────────────────────
    try:
        query = (
            supabase_client.table("call_logs")
            .select(
                "id, tenant_id, phone_number, duration_seconds, "
                "final_state, recording_url, created_at"
            )
            .eq("tenant_id", tenant_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        if search:
            # Supabase ilike filter on phone_number as primary search field
            query = query.ilike("phone_number", f"%{search}%")

        result = query.execute()
        logs = result.data or []

        # Get total count for pagination
        count_result = (
            supabase_client.table("call_logs")
            .select("id", count="exact")
            .eq("tenant_id", tenant_id)
            .execute()
        )
        total = count_result.count if count_result.count is not None else len(logs)

        return {"calls": logs, "total": total, "source": "supabase"}

    except Exception as e:
        if settings.app_env not in ("development", "test"):
            raise HTTPException(status_code=500, detail="Failed to retrieve call logs.")
        # Supabase query failed — degrade gracefully to local file
        logs = []
        if os.path.exists(LOCAL_CALL_LOGS_PATH):
            try:
                with open(LOCAL_CALL_LOGS_PATH, "r") as f:
                    all_logs = json.load(f)
                logs = [lg for lg in all_logs if lg.get("tenant_id") == tenant_id]
            except Exception:
                pass
        logs = sorted(logs, key=lambda x: x.get("created_at", ""), reverse=True)
        page = logs[offset : offset + limit]
        return {"calls": page, "total": len(logs), "source": "local_fallback_error"}


# ====================================================
# CALL DETAIL  —  GET /api/analytics/calls/{call_id}
# ====================================================
@analytics_router.get("/calls/{call_id}")
async def get_call_detail(
    call_id: str,
    user: UserPrincipal = Depends(get_current_user),
):
    """
    Returns the full detail record for a single call, including transcript.
    Enforces tenant isolation: a call owned by another tenant returns 404.

    Added as part of Rec 4 (executive audit): wires the Call Detail page
    to real backend data instead of deterministic mock data.
    """
    tenant_id = user.tenant_id

    # ── Local JSON fallback ─────────────────────────────────────────────────
    if not supabase_client:
        if settings.app_env not in ("development", "test"):
            raise HTTPException(status_code=500, detail="Database connection offline.")
        if os.path.exists(LOCAL_CALL_LOGS_PATH):
            try:
                with open(LOCAL_CALL_LOGS_PATH, "r") as f:
                    all_logs = json.load(f)
                for lg in all_logs:
                    if lg.get("id") == call_id and lg.get("tenant_id") == tenant_id:
                        return {"call": lg, "source": "local_fallback"}
            except Exception:
                pass
        raise HTTPException(status_code=404, detail="Call not found")

    # ── Supabase live path ──────────────────────────────────────────────────
    try:
        result = (
            supabase_client.table("call_logs")
            .select("*")
            .eq("id", call_id)
            .eq("tenant_id", tenant_id)  # Tenant isolation enforced
            .limit(1)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Call not found")
        return {"call": result.data[0], "source": "supabase"}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve call record")
