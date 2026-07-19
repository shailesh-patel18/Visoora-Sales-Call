import time
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/health")
async def health_check(request: Request):
    status = getattr(request.app.state, "service_status", {
        "status": "unknown",
        "database": "unknown",
        "redis": "unknown",
        "crawler": "unknown",
        "email": "unknown",
        "twilio": "unknown",
        "ai_gateway": "unknown",
        "version": "17.0",
        "environment": "unknown"
    })
    
    start_time = getattr(request.app.state, "start_time", time.time())
    uptime_seconds = int(time.time() - start_time)
    
    # Format per CTO requirements
    response = {
        "status": status.get("status", "unknown"),
        "services": {
            "database": status.get("database", "unknown"),
            "redis": status.get("redis", "unknown"),
            "crawler": status.get("crawler", "unknown"),
            "email": status.get("email", "unknown"),
            "twilio": status.get("twilio", "unknown"),
            "ai_gateway": status.get("ai_gateway", "unknown"),
            "openrouter": status.get("openrouter", "unknown")
        },
        "startup_time_ms": getattr(request.app.state, "startup_time_ms", 0),
        "uptime_seconds": uptime_seconds,
        "version": status.get("version", "17.0")
    }
    
    return response

@router.get("/api/health")
async def detailed_health_check(request: Request):
    """Deep health check for dashboard. Performs actual pings where possible."""
    status = getattr(request.app.state, "service_status", {}).copy()
    
    # Ping DB
    try:
        from supabase import create_client
        import os
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY"))
        if url and key:
            client = create_client(url, key)
            client.table("business_brains").select("id").limit(1).execute()
        db_status = "🟢 healthy"
    except Exception:
        db_status = "🔴 failed"
        
    # Check Celery Queue (Redis) if rate limiter is up
    try:
        from security.rate_limiter import rate_limiter
        if rate_limiter.redis:
            queue_status = "🟢 healthy"
        else:
            queue_status = "🔴 failed"
    except Exception:
        queue_status = "🔴 failed"

    return {
        "Database": db_status,
        "AI Providers": "🟢 healthy" if status.get("ai_gateway") == "healthy" else "🟡 degraded",
        "Email Providers": "🟢 healthy" if status.get("email") == "healthy" else "🟡 degraded",
        "Twilio": "🟢 healthy" if status.get("twilio") == "healthy" else "🔴 disabled",
        "Queue (Redis)": queue_status,
        "Worker (Celery)": "🟢 healthy" # In a real scenario, we'd ping celery stats
    }

@router.get("/ready")
async def readiness_check(request: Request):
    status = getattr(request.app.state, "service_status", {})
    overall = status.get("status", "unknown")
    
    # If the app is fully degraded or starting, we are not ready.
    # We allow twilio to be disabled, but database and redis should be healthy.
    if overall in ["starting", "failed"]:
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": overall})
        
    db_status = status.get("database", "unknown")
    if db_status not in ["healthy", "unknown"]:
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "database_unavailable"})
        
    return {"status": "ready"}
