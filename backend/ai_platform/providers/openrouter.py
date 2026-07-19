from typing import Type
from pydantic import BaseModel
from openai import AsyncOpenAI
import instructor
from .base_provider import BaseLLMProvider
from security.config import settings
import structlog

logger = structlog.get_logger("visoora_openrouter")

class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "deepseek/deepseek-chat"):
        self.model_name = model_name
        self.client = instructor.from_openai(
            AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.openrouter_api_key,
            ),
            mode=instructor.Mode.JSON
        )
        self.raw_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )

    @property
    def name(self) -> str:
        return "openrouter"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.raw_client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("openrouter_generate_failed", error=str(e), model=self.model_name)
            raise e

    async def generate_structured(self, prompt: str, schema: Type[BaseModel], system_prompt: str = "") -> BaseModel:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_model=schema,
                max_retries=2
            )
            return response
        except Exception as e:
            logger.error("openrouter_generate_structured_failed", error=str(e), model=self.model_name)
            raise e
