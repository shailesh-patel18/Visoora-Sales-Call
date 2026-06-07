from fastapi import APIRouter, Depends, HTTPException
import json
import asyncio
from typing import Dict, Any
from server.session_registry import redis_client
from server.storage_manager import supabase_client
from security.auth import verify_jwt

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

@analytics_router.get("/dashboard")
async def get_dashboard_metrics(token_payload: dict = Depends(verify_jwt)):
    tenant_id = token_payload.get("tenant_id")
    cache_key = f"analytics:dashboard:{tenant_id}"
    
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
            
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database unconfigured")

    # Aggregate metrics
    logs_res = supabase_client.table("call_logs").select("duration_seconds, final_state").eq("tenant_id", tenant_id).execute()
    logs = logs_res.data or []
    
    total_calls = len(logs)
    total_duration = sum(log.get("duration_seconds", 0) for log in logs)
    success_calls = sum(1 for log in logs if log.get("final_state") in ("SUCCESS_COMPLETE", "BOOKING", "QUALIFICATION"))
    success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0
    
    payload = {
        "total_calls": total_calls,
        "total_duration_seconds": total_duration,
        "success_rate_percent": round(success_rate, 2),
        "success_calls": success_calls
    }
    
    if redis_client:
        redis_client.set(cache_key, json.dumps(payload), ex=300) # 5 minutes cache
        
    return payload

@analytics_router.get("/funnel")
async def get_funnel_metrics(token_payload: dict = Depends(verify_jwt)):
    tenant_id = token_payload.get("tenant_id")
    cache_key = f"analytics:funnel:{tenant_id}"
    
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
            
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database unconfigured")

    deals_res = supabase_client.table("deals").select("stage_id").eq("tenant_id", tenant_id).execute()
    stages_res = supabase_client.table("pipeline_stages").select("id, name, position").eq("tenant_id", tenant_id).order("position").execute()
    
    deals = deals_res.data or []
    stages = stages_res.data or []
    
    stage_counts = {stage["id"]: {"name": stage["name"], "count": 0} for stage in stages}
    
    for deal in deals:
        sid = deal.get("stage_id")
        if sid in stage_counts:
            stage_counts[sid]["count"] += 1
            
    payload = {"funnel": list(stage_counts.values())}
    
    if redis_client:
        redis_client.set(cache_key, json.dumps(payload), ex=300)
        
    return payload

@analytics_router.get("/agents")
async def get_agent_metrics(token_payload: dict = Depends(verify_jwt)):
    # Note: Tenant isolation for global LLM metrics could be omitted, but we return mock global percentiles here
    cache_key = "analytics:agents:latency"
    
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
            
    # Normally we would query a telemetry db or prometheus. 
    # For now, we report simulated percentiles
    payload = {
        "p50_latency_ms": 450,
        "p90_latency_ms": 580,
        "p99_latency_ms": 710,
        "active_fallback_rate": "2.1%"
    }
    
    if redis_client:
        redis_client.set(cache_key, json.dumps(payload), ex=300)
        
    return payload
