import threading
from typing import Dict, Any

class MetricsRegistry:
    """
    Thread-safe global registry for provider metrics.
    Tracks success, failure, and latency across all provider instances.
    """
    def __init__(self):
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _ensure_provider(self, provider_name: str):
        if provider_name not in self._metrics:
            self._metrics[provider_name] = {
                "success_count": 0,
                "failure_count": 0,
                "total_latency_ms": 0.0,
                "status": "healthy"
            }

    def record(self, provider_name: str, success: bool, latency_ms: float):
        with self._lock:
            self._ensure_provider(provider_name)
            
            if success:
                self._metrics[provider_name]["success_count"] += 1
            else:
                self._metrics[provider_name]["failure_count"] += 1
                
            self._metrics[provider_name]["total_latency_ms"] += latency_ms

    def set_status(self, provider_name: str, status: str):
        with self._lock:
            self._ensure_provider(provider_name)
            self._metrics[provider_name]["status"] = status

    def get_all_metrics(self) -> list:
        with self._lock:
            results = []
            for name, data in self._metrics.items():
                total_requests = data["success_count"] + data["failure_count"]
                avg_latency = (data["total_latency_ms"] / total_requests) if total_requests > 0 else 0
                success_rate = (data["success_count"] / total_requests) if total_requests > 0 else 0
                
                results.append({
                    "name": name,
                    "status": data["status"],
                    "success_count": data["success_count"],
                    "failure_count": data["failure_count"],
                    "latency": round(avg_latency, 2),
                    "success_rate": round(success_rate, 2)
                })
            return results

# Singleton instance
global_metrics_registry = MetricsRegistry()
