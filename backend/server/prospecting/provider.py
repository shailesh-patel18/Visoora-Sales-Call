from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .metrics_registry import global_metrics_registry

class ProspectProvider(ABC):
    """
    Abstract Base Class for prospecting providers.
    Providers should inherit from this and one or more Capabilities
    from capability.py.
    """
    def __init__(self):
        # We no longer track metrics locally, we track them globally
        self.cost = 0.0 # Base cost per request (0 for free, higher for paid)

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider (e.g., 'Apollo', 'Mock')."""
        pass

    def report_metric(self, success: bool, latency_ms: float):
        """Track provider performance metrics in the global registry."""
        global_metrics_registry.record(self.name, success, latency_ms)
