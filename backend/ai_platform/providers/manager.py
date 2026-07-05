import structlog
from typing import Any, Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..schemas import ProviderResponse, Capability
from .base import BaseProvider

logger = structlog.get_logger(__name__)

class ProviderManager:
    """
    Dynamically routes AI requests to the best available provider 
    based on the requested capabilities.
    """
    def __init__(self, primary_provider: BaseProvider, fallbacks: List[BaseProvider] = None):
        self.primary = primary_provider
        self.fallbacks = fallbacks or []
        self.providers = [self.primary] + self.fallbacks

    def _select_provider(self, capabilities: List[Capability]) -> BaseProvider:
        """Selects the highest priority provider that supports all required capabilities."""
        if not capabilities:
            return self.primary
            
        for provider in self.providers:
            if all(cap in provider.supported_capabilities for cap in capabilities):
                return provider
                
        # If no provider supports all capabilities, log warning and use primary
        logger.warning("no_provider_for_all_capabilities", capabilities=[c.value for c in capabilities])
        return self.primary

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate_completion(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        capabilities: Optional[List[Capability]] = None
    ) -> ProviderResponse:
        provider = self._select_provider(capabilities or [])
        logger.info("routing_request", task="completion", provider=provider.name)
        
        try:
            return await provider.generate_completion(prompt, system_instruction, capabilities)
        except Exception as e:
            logger.error("provider_error", provider=provider.name, error=str(e))
            # Fallback logic could be inserted here if we want to catch and iterate through fallbacks
            # rather than just relying on tenacity to retry the same provider. 
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate_structured_output(
        self,
        prompt: str,
        schema: Any,
        system_instruction: Optional[str] = None,
        capabilities: Optional[List[Capability]] = None
    ) -> ProviderResponse:
        req_caps = capabilities or []
        if Capability.JSON_SCHEMA not in req_caps:
            req_caps.append(Capability.JSON_SCHEMA)
            
        provider = self._select_provider(req_caps)
        logger.info("routing_request", task="structured_output", provider=provider.name)
        
        try:
            return await provider.generate_structured_output(prompt, schema, system_instruction, req_caps)
        except Exception as e:
            logger.error("provider_error", provider=provider.name, error=str(e))
            raise
