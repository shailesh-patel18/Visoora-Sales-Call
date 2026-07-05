import os
import json
import httpx
import structlog
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = structlog.get_logger("visoora_llm_provider")

class GenerationConfig(BaseModel):
    max_tokens: int = 1000
    temperature: float = 0.7

class LLMProvider(ABC):
    """Abstract Base Class for all LLM interactions in Visoora."""
    
    @abstractmethod
    async def generate_text(self, system_prompt: str, user_prompt: str, config: GenerationConfig = GenerationConfig()) -> str:
        """Generate a text response."""
        pass
        
    @abstractmethod
    async def generate_json(self, system_prompt: str, user_prompt: str, config: GenerationConfig = GenerationConfig()) -> Dict[str, Any]:
        """Generate a structured JSON response."""
        pass

class ClaudeProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-3-5-sonnet-20241022"
        self.base_url = "https://api.anthropic.com/v1/messages"
        
    async def _call_api(self, messages: List[Dict[str, Any]], system_prompt: str, config: GenerationConfig) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                self.base_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.model,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "system": system_prompt,
                    "messages": messages
                }
            )
            if res.status_code != 200:
                logger.error("claude_api_error", status_code=res.status_code, response=res.text)
                res.raise_for_status()
                
            response_json = res.json()
            return response_json["content"][0]["text"]

    async def generate_text(self, system_prompt: str, user_prompt: str, config: GenerationConfig = GenerationConfig()) -> str:
        messages = [{"role": "user", "content": user_prompt}]
        return await self._call_api(messages, system_prompt, config)

    async def generate_json(self, system_prompt: str, user_prompt: str, config: GenerationConfig = GenerationConfig()) -> Dict[str, Any]:
        # Append instruction to return raw JSON to the system prompt
        json_system = system_prompt + "\n\nYou MUST return raw valid JSON. Do not include markdown code blocks or conversational text."
        messages = [{"role": "user", "content": user_prompt}]
        
        response_text = await self._call_api(messages, json_system, config)
        
        try:
            # Simple cleanup for potential markdown blocks
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
                
            return json.loads(clean_text.strip())
        except Exception as e:
            logger.error("claude_json_parse_error", raw_response=response_text, error=str(e))
            raise ValueError(f"Failed to parse Claude JSON response: {e}")

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o"
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
    async def _call_api(self, messages: List[Dict[str, Any]], config: GenerationConfig, response_format: str = "text") -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
            
        payload = {
            "model": self.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "messages": messages
        }
        
        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            if res.status_code != 200:
                logger.error("openai_api_error", status_code=res.status_code, response=res.text)
                res.raise_for_status()
                
            response_json = res.json()
            return response_json["choices"][0]["message"]["content"]

    async def generate_text(self, system_prompt: str, user_prompt: str, config: GenerationConfig = GenerationConfig()) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return await self._call_api(messages, config)

    async def generate_json(self, system_prompt: str, user_prompt: str, config: GenerationConfig = GenerationConfig()) -> Dict[str, Any]:
        json_system = system_prompt + "\n\nYou MUST return raw valid JSON."
        messages = [
            {"role": "system", "content": json_system},
            {"role": "user", "content": user_prompt}
        ]
        response_text = await self._call_api(messages, config, response_format="json_object")
        
        try:
            return json.loads(response_text.strip())
        except Exception as e:
            logger.error("openai_json_parse_error", raw_response=response_text, error=str(e))
            raise ValueError(f"Failed to parse OpenAI JSON response: {e}")

# Factory to get the active provider
def get_llm_provider(provider_name: str = "claude") -> LLMProvider:
    provider_name = os.getenv("DEFAULT_LLM_PROVIDER", provider_name).lower()
    if provider_name == "openai":
        return OpenAIProvider()
    return ClaudeProvider()
