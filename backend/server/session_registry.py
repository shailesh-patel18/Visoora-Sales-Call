import os
import json
import asyncio
import structlog
from typing import Optional, Dict, Any
import redis

# Structured logging setup
logger = structlog.get_logger("visoora_telephony")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ----------------------------------------------------
# REDIS CONNECTION POOL MANAGER WITH GRACEFUL FALLBACK
# ----------------------------------------------------
redis_client: Optional[redis.Redis] = None
try:
    if REDIS_URL:
        # Create connection pool restricting connections to max 50 per pod
        pool = redis.ConnectionPool.from_url(REDIS_URL, max_connections=50, decode_responses=True)
        redis_client = redis.Redis(connection_pool=pool)
        # Ping check
        redis_client.ping()
        logger.info("redis_connected", message="Redis Connection Pool Initialized successfully.", url=REDIS_URL)
except Exception as e:
    redis_client = None
    logger.error("redis_connection_failed", message="Redis unavailable. Cascading to local thread-safe in-memory fallback.", error=str(e))


class SessionRegistry:
    """
    Manages active call session routing and FSM states.
    Ensures horizontal routing affinity (sticky fallback) and stateless pod crash-recovery.
    """
    def __init__(self):
        # Local in-memory thread-safe fallbacks for offline environments
        self._local_sessions: Dict[str, str] = {}
        self._local_states: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def register_session(self, stream_sid: str, pod_id: str):
        """
        Maps a stream_sid to the active handling pod_id.
        Keeps the active streams count key updated for KEDA auto-scaling metrics.
        """
        logger.info("session_register_start", stream_sid=stream_sid, pod_id=pod_id)
        if redis_client:
            try:
                # Store pod routing registry with 1 hour TTL
                redis_client.set(f"visoora:session:{stream_sid}", pod_id, ex=3600)
                
                # Update KEDA metrics registry
                redis_client.sadd("visoora:active_streams_set", stream_sid)
                count = redis_client.scard("visoora:active_streams_set")
                redis_client.set("visoora:active_streams_count", str(count))
                
                logger.info("session_registered_redis", stream_sid=stream_sid, pod_id=pod_id, active_calls=count)
                return
            except Exception as e:
                logger.error("redis_register_failed", message="Redis session registration failed. Falling back.", error=str(e))
                
        async with self._lock:
            self._local_sessions[stream_sid] = pod_id

    async def deregister_session(self, stream_sid: str):
        """Removes session assignment and decrements the active scaling count."""
        logger.info("session_deregister_start", stream_sid=stream_sid)
        if redis_client:
            try:
                redis_client.delete(f"visoora:session:{stream_sid}")
                redis_client.srem("visoora:active_streams_set", stream_sid)
                count = redis_client.scard("visoora:active_streams_set")
                redis_client.set("visoora:active_streams_count", str(count))
                logger.info("session_deregistered_redis", stream_sid=stream_sid, active_calls=count)
                return
            except Exception as e:
                logger.error("redis_deregister_failed", message="Redis session removal failed.", error=str(e))
                
        async with self._lock:
            self._local_sessions.pop(stream_sid, None)

    async def get_session_pod(self, stream_sid: str) -> Optional[str]:
        """Fetches the pod ID currently assigned to the given call stream."""
        if redis_client:
            try:
                pod_id = redis_client.get(f"visoora:session:{stream_sid}")
                if pod_id:
                    return pod_id
            except Exception as e:
                logger.error("redis_get_session_failed", message="Redis session lookup failed.", error=str(e))
                
        async with self._lock:
            return self._local_sessions.get(stream_sid)

    async def persist_call_state(self, stream_sid: str, state_data: dict):
        """
        Stores active call metadata (FSM state, objection count, VAD stats)
        in a Redis hash with a 2-hour TTL for resilient crash recovery.
        """
        if redis_client:
            try:
                key = f"visoora:state:{stream_sid}"
                # Serialize elements to JSON strings
                serialized = {k: json.dumps(v) for k, v in state_data.items()}
                try:
                    redis_client.hset(key, mapping=serialized)
                except Exception:
                    redis_client.hmset(key, serialized)
                redis_client.expire(key, 7200) # 2 hour TTL
                return
            except Exception as e:
                logger.error("redis_persist_state_failed", message="Failed to persist call state in Redis.", error=str(e))
                
        async with self._lock:
            self._local_states[stream_sid] = state_data

    async def load_call_state(self, stream_sid: str) -> Optional[dict]:
        """Reconstitutes active call state mid-session on pod failover."""
        if redis_client:
            try:
                key = f"visoora:state:{stream_sid}"
                raw = redis_client.hgetall(key)
                if raw:
                    return {k: json.loads(v) for k, v in raw.items()}
            except Exception as e:
                logger.error("redis_load_state_failed", message="Failed to load call state from Redis.", error=str(e))
                
        async with self._lock:
            return self._local_states.get(stream_sid)

    async def clear_call_state(self, stream_sid: str):
        """Deletes persistent call state from the cache on clean call finalizations."""
        if redis_client:
            try:
                redis_client.delete(f"visoora:state:{stream_sid}")
            except Exception as e:
                logger.error("redis_clear_state_failed", message="Failed to delete call state from Redis.", error=str(e))
                
        async with self._lock:
            self._local_states.pop(stream_sid, None)

    async def get_active_streams_count(self) -> int:
        """Returns the current number of active streams in the entire cluster."""
        if redis_client:
            try:
                count_str = redis_client.get("visoora:active_streams_count")
                if count_str:
                    return int(count_str)
                return redis_client.scard("visoora:active_streams_set")
            except Exception:
                pass
        async with self._lock:
            return len(self._local_sessions)


# Global singleton registry instance
session_registry = SessionRegistry()
