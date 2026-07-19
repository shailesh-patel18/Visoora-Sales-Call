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
