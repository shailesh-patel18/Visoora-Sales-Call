import structlog
from typing import Optional, Dict, Any
from datetime import datetime
from .storage import TelemetryStorage
import uuid

logger = structlog.get_logger(__name__)

class TelemetryTracker:
    """
    Logs AI telemetry metrics to a provided storage abstraction.
    """
    
    def __init__(self, storage: TelemetryStorage):
        self.storage = storage

    def log_request(
        self,
        tenant_id: str,
        task_name: str,
        provider: str,
        model_name: str,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        step_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        cost_usd: float = 0.0,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        data = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": user_id,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "agent_id": agent_id,
            "task_name": task_name,
            "provider": provider,
            "model_name": model_name,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": cost_usd,
            "status": status,
            "error_message": error_message,
            "created_at": datetime.utcnow().isoformat()
        }

        # Log to structural logger for immediate debugging
        logger.info(
            "ai_request_completed",
            tenant_id=tenant_id,
            task_name=task_name,
            provider=provider,
            model_name=model_name,
            latency_ms=latency_ms,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost_usd,
            status=status
        )

        # Flush to backend storage
        try:
            self.storage.log_request(data)
            self.storage.log_usage(tenant_id, task_name, prompt_tokens + completion_tokens, cost_usd)
        except Exception as e:
            logger.error("telemetry_tracker_flush_failed", error=str(e))
