import asyncio
import signal
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from security.config import settings
from server.worker import start_background_worker
import structlog

logger = structlog.get_logger("visoora_lifespan")

# Note: We import rate_limiter and validation locally to avoid circular imports if necessary
from security.rate_limiter import rate_limiter

def check_dev_env_production_safety():
    if settings.app_env == "development":
        public_domain = os.getenv("SERVER_PUBLIC_DOMAIN", "").strip()
        port = os.getenv("PORT", "8000")
        if public_domain:
            logger.critical(
                "SECURITY WARNING: APP_ENV=development is set but SERVER_PUBLIC_DOMAIN is also configured.",
                event="dev_env_public_domain_mismatch"
            )
        else:
            logger.info(f"APP_ENV=development confirmed.", event="dev_env_localhost_only")

async def handle_graceful_shutdown():
    logger.info("SIGTERM/SIGINT received. Starting graceful shutdown...", event="graceful_shutdown")
    await asyncio.sleep(2)
    os._exit(0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Visoora Backend Lifespan", event="lifespan_start")
    
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
        logger.error(f"Rate limiter connection failed: {e}", event="rate_limiter_fail")
        app.state.service_status["redis"] = "degraded"
        
    # Twilio Boot Time Validation
    try:
        from server.twilio_handler import run_boot_time_validation
        await run_boot_time_validation()
        app.state.service_status["twilio"] = "healthy"
        app.state.service_status["status"] = "healthy"
    except Exception as e:
        logger.error(f"Twilio boot time validation failed: {e}", event="twilio_validation_fail")
        app.state.service_status["twilio"] = "disabled"
        app.state.service_status["status"] = "degraded"
        logger.warning("Voice disabled. Application continuing to boot.", event="voice_disabled")
        
    # Start background worker
    try:
        await start_background_worker()
    except Exception as e:
        logger.error(f"Background worker failed to start: {e}", event="background_worker_fail")

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

    logger.info(f"Visoora Backend Lifespan Startup Complete in {app.state.startup_time_ms}ms", event="lifespan_ready")
    yield
    
    logger.info("Visoora Backend Lifespan Shutdown", event="lifespan_shutdown")
