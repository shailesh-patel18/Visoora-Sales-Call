from typing import Dict, List, Type, Any
from .capability import Capability
from .scoring import ProviderScorer
from .provider import ProspectProvider
import logging

logger = logging.getLogger(__name__)

class CapabilityRegistry:
    def __init__(self):
        self._providers: List[ProspectProvider] = []
        self._scorer = ProviderScorer()

    def register(self, provider: ProspectProvider):
        self._providers.append(provider)
        logger.info(f"Registered provider: {provider.name}")

    def get_providers_for_capability(self, capability: Type[Capability]) -> List[ProspectProvider]:
        return [p for p in self._providers if isinstance(p, capability)]

    def get_best_provider(self, capability: Type[Capability]) -> ProspectProvider:
        valid_providers = self.get_providers_for_capability(capability)
        if not valid_providers:
            raise ValueError(f"No providers registered for capability: {capability.__name__}")

        # Sort providers by score descending
        def get_score(p):
            cost = getattr(p, 'cost', 0.0)
            return self._scorer.calculate_score(p.name, base_cost=cost)

        ranked = sorted(valid_providers, key=get_score, reverse=True)
        best = ranked[0]
        
        # Log decision
        scores = {p.name: get_score(p) for p in ranked}
        logger.info(f"Capability '{capability.__name__}' selected '{best.name}'. Scores: {scores}")
        
        return best

global_capability_registry = CapabilityRegistry()
