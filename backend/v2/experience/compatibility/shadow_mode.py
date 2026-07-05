import time
import structlog
from typing import Callable, Any, Dict
from v2.foundation.events.memory_adapter import event_bus
from v2.foundation.events.bus import BaseDomainEvent

logger = structlog.get_logger("shadow_mode")

class ShadowComparisonEvent(BaseDomainEvent):
    event_name: str = "ShadowComparisonGenerated"

class ShadowRunner:
    """
    Executes a legacy function and a v2 function, returning the legacy result to the user immediately,
    but running the v2 function asynchronously to compare latency, cost, and output quality.
    """
    
    @staticmethod
    async def run(
        tenant_id: str, 
        operation_name: str, 
        legacy_func: Callable, 
        v2_func: Callable, 
        *args, **kwargs
    ) -> Any:
        # 1. Run Legacy (Synchronous for the user)
        start_legacy = time.time()
        legacy_result = await legacy_func(*args, **kwargs) if __import__('inspect').iscoroutinefunction(legacy_func) else legacy_func(*args, **kwargs)
        legacy_latency = time.time() - start_legacy
        
        # 2. Fire and forget v2 (Shadow Execution)
        # In production, use asyncio.create_task or a background queue
        import asyncio
        asyncio.create_task(
            ShadowRunner._run_v2_and_compare(
                tenant_id, operation_name, v2_func, legacy_result, legacy_latency, *args, **kwargs
            )
        )
        
        # 3. Return Legacy Result instantly
        return legacy_result
        
    @staticmethod
    async def _run_v2_and_compare(
        tenant_id: str, 
        operation_name: str, 
        v2_func: Callable, 
        legacy_result: Any, 
        legacy_latency: float, 
        *args, **kwargs
    ):
        start_v2 = time.time()
        try:
            v2_result = await v2_func(*args, **kwargs) if __import__('inspect').iscoroutinefunction(v2_func) else v2_func(*args, **kwargs)
            v2_latency = time.time() - start_v2
            
            # Simplified comparison logic
            # In a real system, you'd use LLM-as-a-judge for semantic similarity
            matches = str(legacy_result) == str(v2_result) 
            
            logger.info(
                "shadow_mode_completed",
                operation=operation_name,
                matches=matches,
                legacy_latency_ms=round(legacy_latency * 1000, 2),
                v2_latency_ms=round(v2_latency * 1000, 2)
            )
            
            evt = ShadowComparisonEvent(
                tenant_id=tenant_id,
                trace_id="system",
                payload={
                    "operation": operation_name,
                    "matches": matches,
                    "legacy_latency": legacy_latency,
                    "v2_latency": v2_latency,
                    "legacy_output": str(legacy_result),
                    "v2_output": str(v2_result)
                }
            )
            await event_bus.publish(evt)
            
        except Exception as e:
            logger.error("shadow_mode_v2_failed", operation=operation_name, error=str(e))
