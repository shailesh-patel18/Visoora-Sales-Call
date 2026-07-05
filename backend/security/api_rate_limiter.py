import time
from typing import Dict
from fastapi import Request, HTTPException
import structlog

logger = structlog.get_logger("api_rate_limiter")

# Fallback in-memory store if Redis is not configured or fails
# Format: { "key": {"count": int, "reset_at": float} }
_MEMORY_STORE: Dict[str, Dict[str, float]] = {}

async def _check_rate_limit(key: str, limit: int, window_seconds: int):
    """
    Checks if the given key has exceeded the limit within the window.
    Raises HTTPException 429 if exceeded.
    """
    try:
        from security.rate_limiter import RedisRateLimiter
        # For a full production implementation, we'd inject the global RedisRateLimiter instance.
        # But for Phase 2 infrastructure, we'll try to connect dynamically or fallback.
        # Alternatively, we just use raw redis.
        import redis.asyncio as aioredis
        import os
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            r = aioredis.from_url(redis_url, decode_responses=True)
            current = await r.get(key)
            if current and int(current) >= limit:
                logger.warning("api_rate_limit_exceeded_redis", key=key, limit=limit)
                raise HTTPException(status_code=429, detail="Too Many Requests. Please try again later.")
            
            pipe = r.pipeline()
            pipe.incr(key)
            if not current:
                pipe.expire(key, window_seconds)
            await pipe.execute()
            await r.aclose()
            return
    except HTTPException:
        raise
    except Exception as e:
        # Fall back to in-memory if Redis throws connection error or is missing
        pass

    # In-memory fallback
    now = time.time()
    record = _MEMORY_STORE.get(key)
    
    if record:
        if now > record["reset_at"]:
            # Expired, reset
            _MEMORY_STORE[key] = {"count": 1, "reset_at": now + window_seconds}
        else:
            if record["count"] >= limit:
                logger.warning("api_rate_limit_exceeded_memory", key=key, limit=limit)
                raise HTTPException(status_code=429, detail="Too Many Requests. Please try again later.")
            _MEMORY_STORE[key]["count"] += 1
    else:
        _MEMORY_STORE[key] = {"count": 1, "reset_at": now + window_seconds}

async def enforce_layered_rate_limits(request: Request, domain: str = None, tenant_id: str = "anonymous"):
    """
    Enforces the layered limits:
    - IP Limit: Max 10 requests per hour per IP
    - Domain Limit: Max 3 requests per hour for the same domain
    - Tenant Limit: For anonymous, global limit to prevent total abuse (e.g. 100/hr)
    """
    client_ip = request.client.host if request.client else "unknown_ip"
    
    # 1. IP Limit
    await _check_rate_limit(f"rate:ip:{client_ip}", limit=10, window_seconds=3600)
    
    # 2. Domain Limit (prevents spamming a competitor's domain)
    if domain:
        await _check_rate_limit(f"rate:domain:{domain}", limit=3, window_seconds=3600)
        
    # 3. Tenant Limit
    await _check_rate_limit(f"rate:tenant:{tenant_id}", limit=100, window_seconds=3600)
