from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..schemas import ProviderResponse, Capability

class LLMProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_capabilities(self) -> List[Capability]:
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validates the provider connection (e.g., API key, permissions).
        Returns True if healthy, raises Exception if misconfigured.
        """
        pass

    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        capabilities: Optional[List[Capability]] = None,
        max_tokens: Optional[int] = None
    ) -> ProviderResponse:
        pass

    @abstractmethod
    async def generate_structured_output(
        self,
        prompt: str,
        schema: Any,
        system_instruction: Optional[str] = None,
        capabilities: Optional[List[Capability]] = None,
        max_tokens: Optional[int] = None
    ) -> ProviderResponse:
        pass
