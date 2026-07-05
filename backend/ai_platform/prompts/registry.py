from typing import Dict, Optional
from ..schemas import PromptSchema, Capability

class PromptRegistry:
    """
    Centralized registry for all AI prompts.
    In Phase 2, this will load from a database or YAML configuration.
    """
    def __init__(self):
        self._prompts: Dict[str, PromptSchema] = {}
        self._register_defaults()

    def _register_defaults(self):
        # Example default prompt registration
        self._prompts["website_analysis_v1"] = PromptSchema(
            id="website_analysis_v1",
            version=1,
            description="Analyzes website text to generate business context and ICPs.",
            supported_capabilities=[Capability.JSON_SCHEMA, Capability.FAST],
            system_instruction="You are a B2B SaaS Growth Strategist. Output valid JSON only."
        )

    def get_prompt(self, prompt_id: str) -> Optional[PromptSchema]:
        return self._prompts.get(prompt_id)

prompt_registry = PromptRegistry()
