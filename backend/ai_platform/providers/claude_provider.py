from typing import Type
from pydantic import BaseModel
from anthropic import AsyncAnthropic
from .base_provider import BaseLLMProvider
from security.config import settings
import structlog
import json

logger = structlog.get_logger("visoora_claude")

class ClaudeProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "claude-3-5-sonnet-20240620"):
        self.model_name = model_name
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=4000,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error("claude_generate_failed", error=str(e), model=self.model_name)
            raise e

    async def generate_structured(self, prompt: str, schema: Type[BaseModel], system_prompt: str = "") -> BaseModel:
        # For Claude, we instruct it to return JSON matching the schema
        schema_json = schema.model_json_schema()
        augmented_prompt = (
            f"{prompt}\n\n"
            f"Please output your response STRICTLY as a JSON object matching this JSON Schema:\n"
            f"{json.dumps(schema_json)}\n\n"
            "Do not include markdown blocks or any other text before or after the JSON."
        )
        
        try:
            response_text = await self.generate(augmented_prompt, system_prompt)
            parsed_json = json.loads(response_text)
            return schema.model_validate(parsed_json)
        except Exception as e:
            logger.error("claude_generate_structured_failed", error=str(e), model=self.model_name)
            raise e
