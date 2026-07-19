import asyncio
import signal
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from security.config import settings
from server.worker import start_background_worker
from utils.logger import log_info, log_warn, log_critical, log_error

# Note: We import rate_limiter and validation locally to avoid circular imports if necessary
from server.services.rate_limiter import rate_limiter

def check_dev_env_production_safety():
    if settings.app_env == "development":
        public_domain = os.getenv("SERVER_PUBLIC_DOMAIN", "").strip()
        port = os.getenv("PORT", "8000")
        if public_domain:
            log_critical(
                "dev_env_public_domain_mismatch",
                "SECURITY WARNING: APP_ENV=development is set but SERVER_PUBLIC_DOMAIN is also configured."
            )
        else:
            log_info("dev_env_localhost_only", f"APP_ENV=development confirmed.")

async def handle_graceful_shutdown():
    log_info("graceful_shutdown", "SIGTERM/SIGINT received. Starting graceful shutdown...")
    await asyncio.sleep(2)
    os._exit(0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    log_info("lifespan_start", "Initializing Visoora Backend Lifespan")
    
    # Initialize service status cache
    app.state.service_status = {
        "status": "starting",
        "database": "healthy",
        "redis": "healthy",
        "supabase": "healthy",
        "ai_gateway": "healthy",
        "openrouter": "healthy",
        "twilio": "pending",
        "email": "healthy",
        "crawler": "healthy",
        "version": "v17",
        "environment": settings.app_env,
        "uptime": 0
    }
    app.state.start_time = time.time()
    
    settings.validate_for_startup()
    check_dev_env_production_safety()
    
    # Rate limiter
    try:
        await rate_limiter.connect()
    except Exception as e:
        log_error("rate_limiter_fail", f"Rate limiter connection failed: {e}")
        app.state.service_status["redis"] = "degraded"
        
    # Twilio Boot Time Validation
    try:
        from server.twilio_handler import run_boot_time_validation
        await run_boot_time_validation()
        app.state.service_status["twilio"] = "healthy"
        app.state.service_status["status"] = "healthy"
    except Exception as e:
        log_error("twilio_validation_fail", f"Twilio boot time validation failed: {e}")
        app.state.service_status["twilio"] = "disabled"
        app.state.service_status["status"] = "degraded"
        log_warn("voice_disabled", "Voice disabled. Application continuing to boot.")
        
    # Start background worker
    try:
        await start_background_worker()
    except Exception as e:
        log_error("background_worker_fail", f"Background worker failed to start: {e}")

    # Register Graceful Shutdown
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(handle_graceful_shutdown()))
    except Exception as e:
        signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(handle_graceful_shutdown()))
        signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(handle_graceful_shutdown()))

    if app.state.service_status["status"] == "starting":
        app.state.service_status["status"] = "healthy"

    app.state.startup_time_ms = int((time.time() - app.state.start_time) * 1000)

    log_info("lifespan_ready", f"Visoora Backend Lifespan Startup Complete in {app.state.startup_time_ms}ms")
    yield
    
    log_info("lifespan_shutdown", "Visoora Backend Lifespan Shutdown")
