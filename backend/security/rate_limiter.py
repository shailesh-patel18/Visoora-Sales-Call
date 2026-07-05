import time
import uuid
import asyncio
from typing import Dict, List, Optional
import redis.asyncio as aioredis
from security.config import settings
from security.errors import RateLimitExceededException
from security.logging import logger

class RedisRateLimiter:
    """
    Implements per-tenant rate-limiting rules (max 10 concurrent calls, 500 calls/day)
    utilizing Redis sliding window sorted sets.
    Cascades gracefully to a thread-safe local in-memory manager on Redis connection outages.
    """
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.is_connected = False
        
        # Local thread-safe in-memory fallback registries
        self._local_daily: Dict[str, List[float]] = {}  # tenant_id -> list of timestamps
        self._local_concurrent: Dict[str, set] = {}     # tenant_id -> set of active call_sids
        self._local_endpoints: Dict[str, List[float]] = {} # endpoint:tenant_id -> list of timestamps
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """
        Attempts to establish connection with the configured Redis instance.
        """
        if not self.redis_url:
            self.is_connected = False
            return False
            
        try:
            self.redis = aioredis.from_url(self.redis_url, socket_timeout=2.0)
            # Send ping to assert active connection
            await self.redis.ping()
            self.is_connected = True
            logger.info("redis_connected", message="Connected to Redis rate limiting registry successfully.")
            return True
        except Exception as e:
            self.is_connected = False
            logger.warn(
                "redis_offline_fallback", 
                message="Redis is offline or unreachable. Falling back to local in-memory rate-limiter.",
                error=str(e)
            )
            return False

    async def acquire_call(self, tenant_id: str, call_sid: str) -> bool:
        """
        Checks rate limits (both 24h count and active concurrency limits) for a tenant.
        If limits are clean, logs the request in the daily sliding window and adds to concurrency count.
        """
        # Ensure connection state check
        if self.redis is None:
            await self.connect()
            
        now = time.time()
        
        # ----------------------------------------------------
        # REDIS PATHWAY
        # ----------------------------------------------------
        if self.is_connected and self.redis:
            daily_key = f"ratelimit:daily:{tenant_id}"
            concurrent_key = f"ratelimit:concurrent:{tenant_id}"
            
            try:
                # 1. Evaluate Concurrency Limit (max 10)
                active_calls = await self.redis.scard(concurrent_key)
                if active_calls >= 10:
                    logger.warn(
                        "rate_limit_concurrency_breached", 
                        message="Tenant concurrent call capacity reached limit.", 
                        tenant_id=tenant_id, 
                        active_calls=active_calls,
                        limit=10
                    )
                    raise RateLimitExceededException(
                        f"Tenant '{tenant_id}' has reached the limit of 10 concurrent active calls."
                    )
                    
                # 2. Evaluate Daily sliding window (max 500 requests / 24h)
                # Purge timestamps older than 24h (86400 seconds)
                await self.redis.zremrangebyscore(daily_key, 0, now - 86400)
                
                daily_count = await self.redis.zcard(daily_key)
                if daily_count >= 500:
                    logger.warn(
                        "rate_limit_daily_breached", 
                        message="Tenant daily call request quota exceeded.", 
                        tenant_id=tenant_id, 
                        daily_calls=daily_count,
                        limit=500
                    )
                    raise RateLimitExceededException(
                        f"Tenant '{tenant_id}' has exceeded the daily call allocation limit of 500 calls."
                    )

                # 3. Commit Daily Ingress and Active Concurrency
                pipe = self.redis.pipeline()
                # Store unique transaction ID in sorted set with timestamp
                pipe.zadd(daily_key, {str(uuid.uuid4()): now})
                # Auto-expiry on sorted set to clean empty records
                pipe.expire(daily_key, 86400)
                # Add call session to concurrency set
                pipe.sadd(concurrent_key, call_sid)
                await pipe.execute()
                
                logger.info(
                    "rate_limit_acquired", 
                    message="Rate limit token acquired successfully.", 
                    tenant_id=tenant_id, 
                    daily_calls=daily_count + 1,
                    concurrent_calls=active_calls + 1
                )
                return True
                
            except RateLimitExceededException:
                raise
            except Exception as e:
                # Force fallback on sudden connection failure mid-flight
                self.is_connected = False
                logger.error("redis_runtime_failure", message="Redis failed mid-request. Falling back to memory.", error=str(e))
                # Fall through to local memory logic

        # ----------------------------------------------------
        # IN-MEMORY FALLBACK PATHWAY
        # ----------------------------------------------------
        async with self._lock:
            # 1. Concurrency limit evaluation
            if tenant_id not in self._local_concurrent:
                self._local_concurrent[tenant_id] = set()
            
            active_calls = len(self._local_concurrent[tenant_id])
            if active_calls >= 10:
                logger.warn(
                    "rate_limit_concurrency_breached_local", 
                    message="Local rate limiter concurrency capacity reached.",
                    tenant_id=tenant_id,
                    active_calls=active_calls
                )
                raise RateLimitExceededException(
                    f"Tenant '{tenant_id}' has reached the limit of 10 concurrent active calls (Local Fallback)."
                )

            # 2. Daily limit evaluation
            if tenant_id not in self._local_daily:
                self._local_daily[tenant_id] = []
                
            timestamps = self._local_daily[tenant_id]
            # Purge timestamps older than 24h
            self._local_daily[tenant_id] = [t for t in timestamps if t > now - 86400]
            daily_count = len(self._local_daily[tenant_id])
            
            if daily_count >= 500:
                logger.warn(
                    "rate_limit_daily_breached_local", 
                    message="Local rate limiter daily quota reached.",
                    tenant_id=tenant_id,
                    daily_calls=daily_count
                )
                raise RateLimitExceededException(
                    f"Tenant '{tenant_id}' has exceeded the daily call allocation limit of 500 calls (Local Fallback)."
                )
                
            # 3. Commit daily request and concurrent session
            self._local_daily[tenant_id].append(now)
            self._local_concurrent[tenant_id].add(call_sid)
            
            logger.info(
                "rate_limit_acquired_local", 
                message="Local rate limit token acquired.", 
                tenant_id=tenant_id, 
                daily_calls=daily_count + 1,
                concurrent_calls=active_calls + 1
            )
            return True

    async def release_call(self, tenant_id: str, call_sid: str):
        """
        Decrements the active call concurrency set for a tenant upon call teardown.
        """
        # Ensure connection state check
        if self.redis is None:
            await self.connect()

        # ----------------------------------------------------
        # REDIS PATHWAY
        # ----------------------------------------------------
        if self.is_connected and self.redis:
            concurrent_key = f"ratelimit:concurrent:{tenant_id}"
            try:
                await self.redis.srem(concurrent_key, call_sid)
                logger.info("rate_limit_released", message="Rate limit concurrency token released.", tenant_id=tenant_id, call_sid=call_sid)
                return
            except Exception as e:
                self.is_connected = False
                logger.error("redis_release_failure", message="Failed to release call in Redis.", error=str(e))
                # Fall through to local memory logic

        # ----------------------------------------------------
        # IN-MEMORY FALLBACK PATHWAY
        # ----------------------------------------------------
        async with self._lock:
            if tenant_id in self._local_concurrent:
                self._local_concurrent[tenant_id].discard(call_sid)
                logger.info(
                    "rate_limit_released_local", 
                    message="Local rate limit concurrency token released.", 
                    tenant_id=tenant_id, 
                    call_sid=call_sid,
                    active_calls=len(self._local_concurrent[tenant_id])
                )

    async def check_rate_limit(self, tenant_id: str, endpoint: str, limit: int, window_seconds: int) -> bool:
        """
        Generic sliding window rate limiter for specific endpoints.
        Raises RateLimitExceededException if exceeded.
        """
        if self.redis is None:
            await self.connect()
            
        now = time.time()
        
        # ----------------------------------------------------
        # REDIS PATHWAY
        # ----------------------------------------------------
        if self.is_connected and self.redis:
            key = f"ratelimit:endpoint:{endpoint}:{tenant_id}"
            try:
                await self.redis.zremrangebyscore(key, 0, now - window_seconds)
                count = await self.redis.zcard(key)
                
                if count >= limit:
                    logger.warn("rate_limit_endpoint_breached", tenant_id=tenant_id, endpoint=endpoint, count=count, limit=limit)
                    raise RateLimitExceededException(f"Rate limit exceeded for {endpoint}.")
                
                pipe = self.redis.pipeline()
                pipe.zadd(key, {str(uuid.uuid4()): now})
                pipe.expire(key, window_seconds)
                await pipe.execute()
                return True
            except RateLimitExceededException:
                raise
            except Exception as e:
                self.is_connected = False
                logger.error("redis_runtime_failure_endpoint", message="Redis failed for endpoint limiter.", error=str(e))
                # Fall through
                
        # ----------------------------------------------------
        # IN-MEMORY FALLBACK PATHWAY
        # ----------------------------------------------------
        async with self._lock:
            key = f"{endpoint}:{tenant_id}"
            if key not in self._local_endpoints:
                self._local_endpoints[key] = []
                
            timestamps = self._local_endpoints[key]
            self._local_endpoints[key] = [t for t in timestamps if t > now - window_seconds]
            count = len(self._local_endpoints[key])
            
            if count >= limit:
                logger.warn("rate_limit_endpoint_breached_local", tenant_id=tenant_id, endpoint=endpoint, count=count, limit=limit)
                raise RateLimitExceededException(f"Rate limit exceeded for {endpoint} (Local).")
                
            self._local_endpoints[key].append(now)
            return True

# Instantiate singleton rate limiter
rate_limiter = RedisRateLimiter(redis_url=settings.redis_url)
