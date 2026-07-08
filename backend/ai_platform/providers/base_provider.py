from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type
from pydantic import BaseModel

class BaseLLMProvider(ABC):
    """
    Abstract Base Class for all LLM providers.
    Enforces a strict contract for text generation and structured outputs.
    """
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generates a standard text response.
        """
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: Type[BaseModel], system_prompt: str = "") -> BaseModel:
        """
        Generates a structured response strictly matching the provided Pydantic schema.
        """
        pass
