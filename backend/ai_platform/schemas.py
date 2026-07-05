from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Capability(str, Enum):
    JSON_SCHEMA = "json_schema"
    VISION = "vision"
    AUDIO = "audio"
    LONG_CONTEXT = "long_context"
    STREAMING = "streaming"
    TOOL_CALLING = "tool_calling"
    FAST = "fast"
    REASONING = "reasoning"

class PromptSchema(BaseModel):
    id: str
    version: int
    owner: str = "system"
    description: str
    supported_capabilities: List[Capability] = Field(default_factory=list)
    system_instruction: str
    evaluation_score: float = 0.0

class ProviderResponse(BaseModel):
    content: Any
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    model_name: str
    provider_name: str
