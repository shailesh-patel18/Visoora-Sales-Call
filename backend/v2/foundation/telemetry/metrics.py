import time
import functools
import structlog
from v2.foundation.context.middleware import get_platform_context

logger = structlog.get_logger("telemetry")

def track_performance(operation_name: str):
    """
    Decorator to track the latency of any async operation and emit it to structured logs.
    Automatically grabs the current PlatformContext for tagging.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            ctx = get_platform_context()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    "operation_performance",
                    operation=operation_name,
                    duration_ms=round(duration * 1000, 2),
                    status="success"
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "operation_performance",
                    operation=operation_name,
                    duration_ms=round(duration * 1000, 2),
                    status="error",
                    error=str(e)
                )
                raise
        return wrapper
    return decorator
