from enum import Enum, auto
from typing import Dict, Any, Callable, Awaitable
import structlog
from v2.foundation.context.middleware import get_platform_context
from v2.foundation.telemetry.metrics import track_performance

logger = structlog.get_logger("tool_registry")

class ToolCapability(Enum):
    SEARCH_COMPANY = auto()
    FIND_PROSPECTS = auto()
    ENRICH_EMAIL = auto()
    READ_WEBSITE = auto()
    SEND_EMAIL = auto()
    SCHEDULE_MEETING = auto()

# A tool implementation is an async function that takes a payload and returns a dictionary
ToolImplementation = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]

class ToolRegistry:
    """
    Abstracts tool execution from agents. Agents ask for a capability, 
    and the Registry maps it to the specific integration (e.g., Apollo, Clay, Clearbit).
    """
    def __init__(self):
        self._registry: Dict[ToolCapability, ToolImplementation] = {}
        
    def register(self, capability: ToolCapability, implementation: ToolImplementation):
        """Registers a specific implementation for a capability."""
        self._registry[capability] = implementation
        logger.info("tool_registered", capability=capability.name, implementation=implementation.__name__)
        
    @track_performance("tool_execution")
    async def execute(self, capability: ToolCapability, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the registered tool for the requested capability.
        """
        if capability not in self._registry:
            logger.error("tool_not_found", capability=capability.name)
            raise ValueError(f"No tool registered for capability: {capability.name}")
            
        implementation = self._registry[capability]
        
        ctx = get_platform_context()
        logger.info("tool_execution_started", capability=capability.name, tenant=ctx.tenant_id if ctx else "none")
        
        try:
            result = await implementation(payload)
            return result
        except Exception as e:
            logger.error("tool_execution_failed", capability=capability.name, error=str(e))
            raise

# Global Instance
tool_registry = ToolRegistry()

# ---------------------------------------------------------
# Example Stubs for Implementations (Adapters)
# ---------------------------------------------------------

async def apollo_search_company_adapter(payload: Dict[str, Any]) -> Dict[str, Any]:
    """An implementation of SEARCH_COMPANY using Apollo.io"""
    await __import__("asyncio").sleep(0.2) # Simulate network
    return {"status": "success", "company_domain": payload.get("domain"), "source": "apollo"}
    
async def clay_search_company_adapter(payload: Dict[str, Any]) -> Dict[str, Any]:
    """An implementation of SEARCH_COMPANY using Clay"""
    await __import__("asyncio").sleep(0.2)
    return {"status": "success", "company_domain": payload.get("domain"), "source": "clay"}

# By default, wire up Apollo, but this can be switched globally in one place without changing Agents.
tool_registry.register(ToolCapability.SEARCH_COMPANY, apollo_search_company_adapter)
