from contextvars import ContextVar
from typing import Optional
from fastapi import Request
from v2.foundation.context.platform_context import PlatformContext
import structlog

logger = structlog.get_logger("context_middleware")

# Global ContextVar for the current request context
_current_context: ContextVar[Optional[PlatformContext]] = ContextVar("platform_context", default=None)

def set_platform_context(ctx: PlatformContext):
    """Sets the platform context for the current async execution scope."""
    _current_context.set(ctx)

def get_platform_context() -> Optional[PlatformContext]:
    """Retrieves the current platform context."""
    return _current_context.get()

async def platform_context_middleware(request: Request, call_next):
    """
    FastAPI middleware to extract tenant and trace IDs from headers
    and inject a PlatformContext into the global ContextVar.
    """
    tenant_id = request.headers.get("x-tenant-id") or "default_tenant"
    user_id = request.headers.get("x-user-id")
    trace_id = request.headers.get("x-trace-id")
    
    ctx_kwargs = {"tenant_id": tenant_id}
    if user_id: ctx_kwargs["user_id"] = user_id
    if trace_id: ctx_kwargs["trace_id"] = trace_id
    
    ctx = PlatformContext(**ctx_kwargs)
    set_platform_context(ctx)
    
    # Bind structlog context variables automatically
    structlog.contextvars.bind_contextvars(
        trace_id=ctx.trace_id,
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id
    )
    
    response = await call_next(request)
    
    # Propagate trace ID back to client
    response.headers["x-trace-id"] = ctx.trace_id
    
    structlog.contextvars.clear_contextvars()
    
    return response
