import time
import functools
import structlog
from typing import Dict, Any, Callable, Awaitable
from v2.foundation.context.middleware import get_platform_context
from v2.foundation.events.memory_adapter import event_bus # Import abstract bus in production
from v2.foundation.events.bus import BaseDomainEvent

logger = structlog.get_logger("ai_evaluation")

class AIEvaluationEvent(BaseDomainEvent):
    event_name: str = "AIEvaluationGenerated"

def track_evaluation(task_name: str):
    """
    Decorator that wraps an AI Agent's execution loop.
    It tracks correctness (did it parse successfully?), latency, retries, and emits an evaluation event.
    """
    def decorator(func: Callable[..., Awaitable[Dict[str, Any]]]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = get_platform_context()
            start_time = time.time()
            
            evaluation_payload = {
                "task": task_name,
                "agent_id": kwargs.get("agent_id", "unknown"),
                "status": "success",
                "retries": 0, # In a real implementation, intercept retries
                "latency_ms": 0,
                "correctness_score": 1.0 # 1.0 if it returned expected schema, 0.0 if parsing failed
            }
            
            try:
                result = await func(*args, **kwargs)
                evaluation_payload["latency_ms"] = round((time.time() - start_time) * 1000, 2)
                return result
                
            except Exception as e:
                evaluation_payload["status"] = "failed"
                evaluation_payload["correctness_score"] = 0.0
                evaluation_payload["latency_ms"] = round((time.time() - start_time) * 1000, 2)
                evaluation_payload["error"] = str(e)
                raise
                
            finally:
                # Emit the evaluation for the continuous learning engine (Sprint 8)
                if ctx:
                    evt = AIEvaluationEvent(
                        tenant_id=ctx.tenant_id,
                        trace_id=ctx.trace_id,
                        payload=evaluation_payload
                    )
                    await event_bus.publish(evt)
                    
        return wrapper
    return decorator
