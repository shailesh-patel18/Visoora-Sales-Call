from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uuid
import traceback
import os
from contextvars import ContextVar

from security.config import settings
from server.lifespan import lifespan
import structlog

logger = structlog.get_logger("visoora_main")

app = FastAPI(title="Visoora Engine", version="1.0.0", lifespan=lifespan)

# Global variables and context for tracing
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="anonymous")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = correlation_id_var.get()
    logger.error("unhandled_exception", exception=str(exc), correlation_id=correlation_id, method=request.method, url=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal Server Error", "detail": str(exc)},
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "Validation Error", "detail": exc.errors()},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/recordings", StaticFiles(directory="recordings"), name="recordings")

@app.middleware("http")
async def exception_tracing_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    request.state.correlation_id = correlation_id
    
    auth_header = request.headers.get("Authorization")
    tenant_id = "anonymous"
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            import jwt
            payload = jwt.decode(token, options={"verify_signature": False})
            tenant_id = payload.get("tenant_id") or "default"
        except Exception:
            pass
    tenant_id_var.set(tenant_id)

    import time
    start_time = time.time()
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Don't log health/metrics checks to avoid spam
        if request.url.path not in ["/health", "/ready", "/metrics"]:
            log_structured(
                "INFO", "http_request", 
                f"{request.method} {request.url.path} {response.status_code}", 
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    except Exception as exc:
        log_payload = {
            "traceback": traceback.format_exc(),
            "path": request.url.path,
            "method": request.method
        }
        log_structured("CRITICAL", "http_request_failed", f"Unhandled HTTP exception: {exc}", correlation_id=correlation_id, **log_payload)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "correlation_id": correlation_id}
        )

# ----------------------------------------------------
# ROUTER REGISTRATION
# ----------------------------------------------------
from server.health import router as health_router
app.include_router(health_router)

from server.analytics_api import analytics_router
from server.public_api import public_router
from server.services.business_activation import activation_router
from server.mission_api import mission_router

app.include_router(analytics_router, prefix="/api")
app.include_router(public_router)
app.include_router(activation_router)
app.include_router(mission_router)

# Note: We must also import the Twilio handler so it registers its router
try:
    from server.twilio_handler import router as twilio_router
    app.include_router(twilio_router)
except ImportError as e:
    log_structured("ERROR", "twilio_router_import_failed", str(e))

try:
    from crm.router import router as crm_router
    app.include_router(crm_router)
except ImportError:
    pass

try:
    from server.inbound_handler import inbound_router
    app.include_router(inbound_router)
except ImportError:
    pass

try:
    from services.sms import sms_router
    app.include_router(sms_router)
except ImportError:
    pass

try:
    from server.onboarding_api import router as onboarding_router
    app.include_router(onboarding_router)
except ImportError:
    pass

try:
    from server.job_router import router as job_router
    app.include_router(job_router)
except ImportError:
    pass

try:
    from billing.router import billing_router
    app.include_router(billing_router)
except ImportError:
    pass

try:
    from sales_employee.router import sales_employee_router, public_sales_router
    from server.ws_mission_router import ws_mission_router
    app.include_router(sales_employee_router)
    app.include_router(public_sales_router)
    app.include_router(ws_mission_router)
except ImportError:
    pass

try:
    from security.auth_router import auth_router
    app.include_router(auth_router, prefix="/api/v1")
except ImportError:
    pass

try:
    from server.draft_router import router as draft_router
    from server.events_api import router as events_router
    app.include_router(draft_router, prefix="/api/v1")
    app.include_router(events_router)
except ImportError:
    pass
