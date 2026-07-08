from typing import Type
from pydantic import BaseModel
from openai import AsyncOpenAI
from .base_provider import BaseLLMProvider
from security.config import settings
import structlog

logger = structlog.get_logger("visoora_openai")

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("openai_generate_failed", error=str(e), model=self.model_name)
            raise e

    async def generate_structured(self, prompt: str, schema: Type[BaseModel], system_prompt: str = "") -> BaseModel:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=messages,
                response_format=schema
            )
            return response.choices[0].message.parsed
        except Exception as e:
            logger.error("openai_generate_structured_failed", error=str(e), model=self.model_name)
            raise e
