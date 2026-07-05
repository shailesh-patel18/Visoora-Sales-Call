from enum import Enum, auto
from typing import List

class AICapability(Enum):
    FAST = auto()
    CHEAP = auto()
    REASONING = auto()
    LONG_CONTEXT = auto()
    VISION = auto()
    JSON_MODE = auto()
    TOOL_CALLING = auto()
    AUDIO = auto()

class ModelProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"

class ModelDeployment:
    def __init__(self, provider: ModelProvider, model_name: str, capabilities: List[AICapability], cost_per_1k: float):
        self.provider = provider
        self.model_name = model_name
        self.capabilities = set(capabilities)
        self.cost_per_1k = cost_per_1k

# Global Registry of Available Models
AVAILABLE_MODELS = [
    ModelDeployment(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4o",
        capabilities=[AICapability.REASONING, AICapability.JSON_MODE, AICapability.TOOL_CALLING, AICapability.VISION],
        cost_per_1k=0.005
    ),
    ModelDeployment(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4o-mini",
        capabilities=[AICapability.FAST, AICapability.CHEAP, AICapability.JSON_MODE, AICapability.TOOL_CALLING],
        cost_per_1k=0.00015
    ),
    ModelDeployment(
        provider=ModelProvider.GEMINI,
        model_name="gemini-1.5-flash",
        capabilities=[AICapability.FAST, AICapability.CHEAP, AICapability.LONG_CONTEXT, AICapability.JSON_MODE],
        cost_per_1k=0.000075
    ),
    ModelDeployment(
        provider=ModelProvider.GEMINI,
        model_name="gemini-1.5-pro",
        capabilities=[AICapability.REASONING, AICapability.LONG_CONTEXT, AICapability.VISION, AICapability.AUDIO],
        cost_per_1k=0.0035
    )
]

class CapabilityRouter:
    """
    Selects the optimal model based on the requested capabilities and cost optimization.
    """
    
    @staticmethod
    def resolve_model(required_capabilities: List[AICapability], optimize_for_cost: bool = True) -> ModelDeployment:
        req_set = set(required_capabilities)
        
        # Filter models that have ALL required capabilities
        candidates = [m for m in AVAILABLE_MODELS if req_set.issubset(m.capabilities)]
        
        if not candidates:
            raise ValueError(f"No model found supporting capabilities: {required_capabilities}")
            
        if optimize_for_cost or AICapability.CHEAP in req_set:
            # Sort by cost ascending
            candidates.sort(key=lambda m: m.cost_per_1k)
            
        return candidates[0]
