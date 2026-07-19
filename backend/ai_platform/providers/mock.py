import os
from typing import Optional, List, Any
from .base import LLMProvider
from ..schemas import ProviderResponse, Capability
from pydantic import BaseModel
import time

class MockLLMProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "mock_llm"
        
    @property
    def supported_capabilities(self) -> List[Capability]:
        return [
            Capability.JSON_SCHEMA,
            Capability.FAST,
        ]

    async def validate_connection(self) -> bool:
        return True

    async def generate_completion(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        capabilities: Optional[List[Capability]] = None,
        max_tokens: Optional[int] = None
    ) -> ProviderResponse:
        return ProviderResponse(
            provider_name=self.name,
            model_name="mock-model",
            content="This is a mock text completion.",
            prompt_tokens=10,
            completion_tokens=20,
            latency_ms=100
        )

    async def generate_structured_output(
        self,
        prompt: str,
        schema: Any,
        system_instruction: Optional[str] = None,
        capabilities: Optional[List[Capability]] = None,
        max_tokens: Optional[int] = None
    ) -> ProviderResponse:
        # If schema is a Pydantic model, we can try to return a dummy instance
        if issubclass(schema, BaseModel):
            dummy_data = {}
            for field_name, field_info in schema.model_fields.items():
                if field_info.annotation == str:
                    dummy_data[field_name] = "Mock String"
                elif field_info.annotation == int:
                    dummy_data[field_name] = 42
                else:
                    dummy_data[field_name] = None
            obj = schema(**dummy_data)
        else:
            obj = None
            
        return ProviderResponse(
            provider_name=self.name,
            model_name="mock-model",
            content=obj,
            prompt_tokens=10,
            completion_tokens=20,
            latency_ms=100
        )
