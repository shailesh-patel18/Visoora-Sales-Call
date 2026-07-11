import os
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types

from ..schemas import ProviderResponse, Capability
from .base import BaseProvider

class GeminiProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.default_model = "gemini-2.5-flash"

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def supported_capabilities(self) -> List[Capability]:
        return [
            Capability.JSON_SCHEMA,
            Capability.VISION,
            Capability.AUDIO,
            Capability.LONG_CONTEXT,
            Capability.STREAMING,
            Capability.TOOL_CALLING,
            Capability.FAST,
            Capability.REASONING
        ]

    def _determine_model(self, capabilities: List[Capability]) -> str:
        if Capability.REASONING in capabilities:
            return "gemini-2.5-pro"
        return "gemini-2.5-flash"

    async def generate_completion(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        capabilities: Optional[List[Capability]] = None,
        max_tokens: Optional[int] = None
    ) -> ProviderResponse:
        model_name = self._determine_model(capabilities or [])
        
        config_kwargs = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens
            
        start_time = time.time()
        
        # Note: the new google-genai SDK uses synchronous or asynchronous methods. 
        # Using aio for async support.
        response = await self.client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return ProviderResponse(
            content=response.text,
            latency_ms=latency_ms,
            prompt_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
            completion_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            model_name=model_name,
            provider_name=self.name
        )

    async def generate_structured_output(
        self,
        prompt: str,
        schema: Any,
        system_instruction: Optional[str] = None,
        capabilities: Optional[List[Capability]] = None,
        max_tokens: Optional[int] = None
    ) -> ProviderResponse:
        model_name = self._determine_model(capabilities or [])
        
        # Inject the schema into the system instruction to avoid Gemini's strict state limit
        schema_json = schema.schema_json() if hasattr(schema, "schema_json") else str(schema)
        enhanced_instruction = f"{system_instruction or ''}\n\nYou MUST return a valid JSON object matching this schema:\n{schema_json}"
        
        config_kwargs = {
            "response_mime_type": "application/json",
            "system_instruction": enhanced_instruction
        }
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens
            
        start_time = time.time()
        
        response = await self.client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs)
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # The content should be parsed as JSON matching the Pydantic schema
        import json
        try:
            parsed_content = schema.model_validate_json(response.text)
        except Exception as e:
            # Simple repair or fallback could happen here
            parsed_content = json.loads(response.text) # raw fallback
            
        return ProviderResponse(
            content=parsed_content,
            latency_ms=latency_ms,
            prompt_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
            completion_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            model_name=model_name,
            provider_name=self.name
        )
