import structlog
from typing import Optional, Dict, Any, List

from ..providers.manager import ProviderManager
from ..providers.gemini import GeminiProvider
from ..prompts.registry import prompt_registry
from ..schemas import Capability
from ..policy import PolicyLayer
from ..telemetry import telemetry_tracker

logger = structlog.get_logger(__name__)

class BaseAgent:
    """
    The base class for all AI Agents in Visoora.
    It encapsulates the ProviderManager, PolicyLayer, and Telemetry,
    so that application logic doesn't touch LLMs directly.
    """
    def __init__(self, tenant_id: str, user_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        import os
        is_dev = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
        if is_dev:
            from ..providers.mock import MockLLMProvider
            primary = MockLLMProvider()
        else:
            from ..providers.gemini import GeminiProvider
            primary = GeminiProvider()
            
        self.provider_manager = ProviderManager(primary_provider=primary)
        
    async def execute_task(
        self, 
        task_name: str, 
        prompt_id: str, 
        context: str, 
        schema: Optional[Any] = None,
        extra_capabilities: Optional[List[Capability]] = None,
        max_tokens: Optional[int] = 4000,
        memory: Optional[Any] = None
    ) -> Any:
        
        if not PolicyLayer.validate_request(self.tenant_id, task_name, {"context": context}):
            raise PermissionError("Policy violation or permissions error.")
            
        prompt = prompt_registry.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt ID {prompt_id} not found in registry.")
            
        capabilities = list(set(prompt.supported_capabilities + (extra_capabilities or [])))
        
        try:
            if schema:
                # If a schema is provided, we expect structured output
                res = await self.provider_manager.generate_structured_output(
                    prompt=context,
                    schema=schema,
                    system_instruction=prompt.system_instruction,
                    capabilities=capabilities,
                    max_tokens=max_tokens
                )
            else:
                # Otherwise, text completion
                res = await self.provider_manager.generate_completion(
                    prompt=context,
                    system_instruction=prompt.system_instruction,
                    capabilities=capabilities,
                    max_tokens=max_tokens
                )
                
            if memory:
                # Log prompt versioning to memory
                prompts_used = memory.get("metadata").get("prompts_used", {})
                prompts_used[task_name] = {
                    "id": prompt.id,
                    "version": prompt.version,
                    "model": prompt.model or res.model_name,
                    "temperature": prompt.temperature
                }
                memory.update_metadata("prompts_used", prompts_used)
                
            telemetry_tracker.log_request(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                task_name=task_name,
                provider=res.provider_name,
                model_name=res.model_name,
                latency_ms=res.latency_ms,
                prompt_tokens=res.prompt_tokens,
                completion_tokens=res.completion_tokens,
                status="success"
            )
            return res.content
            
        except Exception as e:
            telemetry_tracker.log_request(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                task_name=task_name,
                provider="unknown",
                model_name="unknown",
                latency_ms=0,
                prompt_tokens=0,
                completion_tokens=0,
                status="failed",
                error_message=str(e)
            )
            raise
