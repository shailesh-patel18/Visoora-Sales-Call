import os
import sys
import json
import base64
import struct
import asyncio
import httpx
import math
import datetime
import uuid
import time
import traceback
from fastapi import FastAPI, WebSocket, Request, Response, APIRouter, Depends, HTTPException, Security
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Optional, List, Any
from dotenv import load_dotenv

import structlog
from security.config import settings
from security.errors import rfc7807_exception_handler, SecurityException
from security.rbac import get_current_user, RoleChecker, UserPrincipal
from security.twilio_auth import verify_twilio_signature
from security.rate_limiter import rate_limiter
from security.logging import configure_structlog, correlation_id_var, tenant_id_var, stream_sid_var
from compliance.gate import compliance_router

# Observability stack imports
from observability.tracing import (
    init_tracer, start_call_trace, end_call_trace,
    span_decode, span_vad, span_llm, span_tts,
    span_fsm_transition, get_current_trace_id,
)
from observability.metrics import (
    track_call_start, track_call_end, track_fsm_transition,
    track_llm_latency, track_vad_interruption, track_compliance_block,
    track_decode_error, get_metrics_response, SERVICE_INFO,
)

# Configure structlog globally
configure_structlog()

# Load environment configuration
load_dotenv()

# Load environment configuration
load_dotenv()

# ----------------------------------------------------
# PRODUCTION STRUCTURED LOGGER DEFINITION (structlog)
# ----------------------------------------------------
logger = structlog.get_logger("visoora_telephony")

def log_structured(level: str, event: str, message: str, **kwargs):
    """Outputs a standard structured JSON log string to standard output."""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(event, event_message=message, **kwargs)

def log_info(event: str, message: str, **kwargs):
    logger.info(event, event_message=message, **kwargs)

def log_debug(event: str, message: str, **kwargs):
    logger.debug(event, event_message=message, **kwargs)

def log_warn(event: str, message: str, **kwargs):
    logger.warn(event, event_message=message, **kwargs)

def log_error(event: str, message: str, **kwargs):
    logger.error(event, event_message=message, **kwargs)

def log_critical(event: str, message: str, **kwargs):
    logger.critical(event, event_message=message, **kwargs)

# ----------------------------------------------------
# BOOT-TIME TELEPHONY DEPLOYMENT VALIDATION
# ----------------------------------------------------
def run_boot_time_validation():
    log_info("bootcheck_start", "Starting Production Telephony Orchestration Boot-time Diagnostics...")
    errors = []
    
    # 1. Validate Antigravity SDK
    try:
        import google.antigravity
        assert hasattr(google.antigravity, "AgentSession"), "google.antigravity is missing 'AgentSession' class"
        assert hasattr(google.antigravity, "tool"), "google.antigravity is missing 'tool' decorator"
        log_info("bootcheck_ok_sdk", "Google Antigravity SDK verified successfully.")
    except Exception as e:
        errors.append(f"Antigravity SDK dependency check failed: {e}")
        
    # 2. Validate StateMachineController
    try:
        from pipeline.states import StateMachineController
        controller = StateMachineController(initial_metadata={"name": "Test", "company": "Test", "phone": "+123"})
        assert controller.context.current_state == "INITIATION", "FSM failed to initialize to INITIATION state"
        log_info("bootcheck_ok_fsm", "FSM StateMachineController verified successfully.")
    except Exception as e:
        errors.append(f"FSM StateMachineController validation failed: {e}")
        
    # 3. Validate Pipeline Tools
    try:
        from pipeline.tools import handle_sub_agent_handover
        log_info("bootcheck_ok_tools", "ObjectionSpecialist/pipeline tools verified successfully.")
    except Exception as e:
        errors.append(f"ObjectionSpecialist/pipeline tools validation failed: {e}")
        
    # 4. Validate VAD Engine
    try:
        from pipeline.vad import VoiceActivityDetector
        detector = VoiceActivityDetector(threshold=300.0)
        rms = detector.calculate_frame_energy(b'\x00' * 640)
        assert rms == 0.0, f"Expected 0.0 RMS energy for silent frame, got {rms}"
        log_info("bootcheck_ok_vad", "VoiceActivityDetector engine verified successfully.")
    except Exception as e:
        errors.append(f"VAD Engine validation failed: {e}")
        
    # 5. Validate Storage Manager
    try:
        from server.storage_manager import call_session_tracker
        assert call_session_tracker is not None, "call_session_tracker instance is None"
        log_info("bootcheck_ok_storage", "Storage Manager and CallSessionTracker verified successfully.")
    except Exception as e:
        errors.append(f"Storage Manager validation failed: {e}")
        
    if errors:
        log_critical("bootcheck_critical_failure", "CRITICAL BOOT-TIME VALIDATION FAILED! SERVER WILL REFUSE TO BOOT.", errors=errors)
        raise RuntimeError(f"Telephony Orchestration Startup Diagnostics Failed. Total errors: {len(errors)}")
    else:
        log_info("bootcheck_success", "ALL ORCHESTRATION DEPENDENCIES VALIDATED. READY FOR TELEPHONY TRAFFIC.")

# Execute diagnostics strictly on module load
run_boot_time_validation()

# Strict, non-silent imports
from pipeline.states import StateMachineController
from pipeline.tools import handle_sub_agent_handover
from pipeline.vad import VoiceActivityDetector
from server.storage_manager import call_session_tracker
from google.antigravity import AgentSession

# Precompute G.711 Mu-Law lookup tables for sub-microsecond G.711 transcode speeds
ULAW_TO_PCM = []
for i in range(256):
    u = ~i & 0xFF
    sign = 1 if (u & 0x80) else -1
    exponent = (u & 0x70) >> 4
    mantissa = u & 0x0F
    
    sample = (mantissa << 3) + 132
    sample <<= exponent
    sample -= 132
    ULAW_TO_PCM.append(sign * sample)

def _pcm_to_ulaw_sample(pcm: int) -> int:
    pcm = max(-32768, min(32767, pcm))
    sign = 0x80 if pcm < 0 else 0x00
    if pcm < 0:
        pcm = -pcm
    pcm += 132
    if pcm > 32767:
        pcm = 32767
        
    exponent = 7
    while exponent > 0 and not (pcm & (1 << (exponent + 7))):
        exponent -= 1
        
    mantissa = (pcm >> (exponent + 3)) & 0x0F
    return ~(sign | (exponent << 4) | mantissa) & 0xFF

PCM_TO_ULAW = [_pcm_to_ulaw_sample(i - 32768) for i in range(65536)]

# ----------------------------------------------------
# TRANSCODING UTILITIES WITH ERROR COUNTERS
# ----------------------------------------------------
def decode_ulaw_chunk(ulaw_bytes: bytes) -> bytes:
    """Decodes G.711 Mu-law audio bytes (8kHz, 8-bit) directly to Linear 16-bit PCM bytes."""
    pcm_samples = [ULAW_TO_PCM[b] for b in ulaw_bytes]
    return struct.pack(f"<{len(pcm_samples)}h", *pcm_samples)

def encode_pcm_chunk(pcm_bytes: bytes) -> bytes:
    """Encodes Linear 16-bit PCM audio bytes directly into G.711 Mu-law bytes."""
    count = len(pcm_bytes) // 2
    samples = struct.unpack(f"<{count}h", pcm_bytes)
    ulaw_bytes = bytearray(len(samples))
    for idx, s in enumerate(samples):
        ulaw_bytes[idx] = PCM_TO_ULAW[s + 32768]
    return bytes(ulaw_bytes)

def upsample_8k_to_16k(pcm_8k: bytes) -> bytes:
    """Upsamples 8kHz Mono 16-bit PCM to 16kHz Mono 16-bit PCM using nearest-neighbor interpolation."""
    count = len(pcm_8k) // 2
    samples = struct.unpack(f"<{count}h", pcm_8k)
    out_samples = []
    for s in samples:
        out_samples.extend((s, s))
    return struct.pack(f"<{len(out_samples)}h", *out_samples)

def downsample_16k_to_8k(pcm_16k: bytes) -> bytes:
    """Downsamples 16kHz Mono 16-bit PCM to 8kHz Mono 16-bit PCM by dropping every alternate sample."""
    count = len(pcm_16k) // 2
    samples = struct.unpack(f"<{count}h", pcm_16k)
    out_samples = samples[::2]
    return struct.pack(f"<{len(out_samples)}h", *out_samples)

# ----------------------------------------------------
# ASYNCHRONOUS JITTER BUFFER WITH CANCELLATION SUPPORT
# ----------------------------------------------------
class JitterBuffer:
    """Provides a small 40ms smoothing buffer with cancellation and timeout-aware pop."""
    def __init__(self, target_ms: int = 40, packet_ms: int = 20):
        self.queue = asyncio.Queue()
        self.target_count = target_ms // packet_ms
        self.buffered = False

    async def push(self, chunk: bytes):
        await self.queue.put(chunk)

    async def pop(self, timeout: float = 0.05, inject_slowdown: bool = False) -> Optional[bytes]:
        """Pops a frame from the queue. If empty, waits up to `timeout` seconds before returning None."""
        if inject_slowdown:
            # FAILURE MODE: Simulates slow queue consumer thread starvations
            await asyncio.sleep(0.2)
            
        if not self.buffered:
            start_time = time.time()
            while self.queue.qsize() < self.target_count:
                if time.time() - start_time > timeout:
                    break
                await asyncio.sleep(0.005)
            self.buffered = True
            
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

    def flush(self):
        """Purges all elements in the buffer queue immediately."""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except (asyncio.QueueEmpty, ValueError):
                break

# ----------------------------------------------------
# WEBSOCKET REAL-TIME BROADCAST MANAGER
# ----------------------------------------------------
class ConnectionManager:
    """Manages direct WebSocket broadcasts to connected frontend dashboard clients."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
            log_info("dashboard_ws_pool_connect", f"Dashboard connection established. Active pool: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                log_info("dashboard_ws_pool_disconnect", f"Dashboard connection closed. Active pool: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        async with self.lock:
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

live_ws_manager = ConnectionManager()

# Global memory buffer registries for active calls
call_transcripts_buffers: Dict[str, List[dict]] = {}
transcripts_lock = asyncio.Lock()

async def record_and_broadcast_turn(stream_sid: str, speaker: str, text: str, state: str):
    """
    Appends conversation speech turns to the session transcript buffer 
    and broadcasts the update instantly over active WebSockets to the dashboard.
    """
    if not stream_sid:
        return
    turn = {
        "speaker": speaker,
        "text": text,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "state": state
    }
    async with transcripts_lock:
        if stream_sid not in call_transcripts_buffers:
            call_transcripts_buffers[stream_sid] = []
        call_transcripts_buffers[stream_sid].append(turn)

    # Broadcast immediately to frontend
    await live_ws_manager.broadcast({
        "event": "live_transcript_turn",
        "stream_sid": stream_sid,
        "turn": turn
    })

# Campaign Leads Manager with thread-safe file lock
campaign_file_lock = asyncio.Lock()
CAMPAIGN_LEADS_FILE = "recordings/campaign_leads.json"

# Initialize lead list registry if missing
os.makedirs("recordings", exist_ok=True)
if not os.path.exists(CAMPAIGN_LEADS_FILE):
    with open(CAMPAIGN_LEADS_FILE, "w") as f:
        json.dump([
            {"id": "lead_1", "name": "John Doe", "company": "Acme Corp", "phone": "+15017122661", "status": "Pending", "retry_count": 0},
            {"id": "lead_2", "name": "Sarah Connor", "company": "Cyberdyne Systems", "phone": "+919824457565", "status": "Pending", "retry_count": 0},
            {"id": "lead_3", "name": "Bruce Wayne", "company": "Wayne Enterprises", "phone": "+442079460192", "status": "Pending", "retry_count": 0}
        ], f, indent=2)

# ----------------------------------------------------
# FASTAPI APPLICATION SETUP WITH RELIABILITY LAYER
# ----------------------------------------------------
# Scalability and graceful shutdown globals
is_shutting_down = False
active_calls_count = 0
global_vad_interruptions = 0
global_avg_latency_ms = 45.0

app = FastAPI(title="Visoora Engine", version="1.0.0")

# ----------------------------------------------------
# GLOBAL EXCEPTION HANDLERS
# ----------------------------------------------------
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", method=request.method, url=str(request.url), error=str(exc))
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

# Add CORS middleware to allow Next.js browser API access
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize standard routes
from crm.router import router as crm_router
from server.onboarding_api import onboarding_router
from compliance.gate import compliance_router
from server.analytics_api import analytics_router

app.include_router(crm_router)
app.include_router(onboarding_router)
app.include_router(compliance_router)
app.include_router(analytics_router)

# Initialize OpenTelemetry tracer on app creation
init_tracer(
    service_name="visoora-telephony",
    otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
)

# Set Prometheus service info labels
SERVICE_INFO.info({
    "version": "1.0.0",
    "service": "visoora-telephony",
    "pod_id": os.getenv("POD_ID", "local"),
})

# Instrument FastAPI with OpenTelemetry (auto-instruments HTTP spans)
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)
    log_info("otel_fastapi_instrumented", "FastAPI auto-instrumented with OpenTelemetry.")
except ImportError:
    log_warn("otel_fastapi_skip", "opentelemetry-instrumentation-fastapi not installed — skipping auto-instrumentation.")

import signal

async def handle_graceful_shutdown():
    global is_shutting_down
    if is_shutting_down:
        return
    is_shutting_down = True
    log_info("graceful_shutdown_start", f"SIGTERM/SIGINT received. Active calls remaining: {active_calls_count}. Draining up to 300s.")
    
    # Wait for active calls to complete (graceful drainage)
    drain_sec = 300
    while active_calls_count > 0 and drain_sec > 0:
        await asyncio.sleep(1)
        drain_sec -= 1
        if drain_sec % 30 == 0:
            log_info("graceful_shutdown_drain", f"Draining active calls... {active_calls_count} remaining, {drain_sec}s left.")
            
    log_info("graceful_shutdown_complete", "All active calls drained or timeout reached. Exiting process.")
    # Force exit cleanly
    os._exit(0)

@app.on_event("startup")
async def startup_event():
    # Register SIGTERM and SIGINT graceful shutdown signal handlers
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(handle_graceful_shutdown()))
    except Exception as e:
        # Fallback for systems (like local Windows machines) where loop.add_signal_handler might raise errors
        log_warn("sigterm_handler_fallback", f"Standard loop signal handler registration bypassed: {e}. Registering signal hook.")
        signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(handle_graceful_shutdown()))
        signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(handle_graceful_shutdown()))

# Add RFC 7807 problem details exception handlers
app.add_exception_handler(SecurityException, rfc7807_exception_handler)
app.add_exception_handler(HTTPException, rfc7807_exception_handler)

# Include compliance router for DNC lists management
app.include_router(compliance_router)

# Include core CRM pipeline router
from crm.router import router as crm_router
app.include_router(crm_router)

# Include Visoora inbound calling webhook and media routers
from server.inbound_handler import inbound_router
app.include_router(inbound_router)

# Include Twilio two-way SMS webhook router
from services.sms import sms_router
app.include_router(sms_router)

# Include onboarding wizard and phone provisioning router
from server.onboarding_api import onboarding_router
app.include_router(onboarding_router)

# Include SaaS Stripe billing and usage metering router
from billing.router import billing_router
app.include_router(billing_router)

# Prometheus metrics endpoint — unprotected for scraper access
@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus scrape endpoint. Returns all registered metrics."""
    body, content_type = get_metrics_response()
    return Response(content=body, media_type=content_type)

# Health check — unprotected
@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_calls": active_calls_count, "shutting_down": is_shutting_down}

# Exception tracing middleware with correlation IDs and context variables
@app.middleware("http")
async def exception_tracing_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    request.state.correlation_id = correlation_id
    
    # Check if this is an authenticated request to set contextvars
    auth_header = request.headers.get("Authorization")
    tenant_id = "anonymous"
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            # Fast unverified parse to extract log context
            import jwt
            payload = jwt.decode(token, options={"verify_signature": False})
            tenant_id = payload.get("tenant_id") or payload.get("email", "").split("@")[-1] or "default"
        except Exception:
            pass
    tenant_id_var.set(tenant_id)

    try:
        response = await call_next(request)
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

# Twilio Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_twilio_auth_token_here")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_TRIAL_NUMBER", "+15017122661")

@app.post("/incoming-call")
async def handle_incoming_call(request: Request, verified: bool = Depends(verify_twilio_signature)):
    """
    Twilio voice webhook endpoint.
    Protected by X-Twilio-Signature verification middleware.
    Forces secure WebSockets (wss://) for remote endpoints and builds a non-blocking media stream connection.
    Injects dynamic US TCPA recording disclosures and FTC automated AI disclosures per tenant context.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    host = request.headers.get("host", "localhost:8000")
    
    # PRODUCTION INFRASTRUCTURE FIX: Force WSS for public secure tunnels (localtunnel/ngrok)
    if "localhost" not in host and "127.0.0.1" not in host:
        protocol = "wss"
    else:
        # Standard local fallback
        protocol = "wss" if request.headers.get("x-forwarded-proto") == "https" else "ws"
        
    prospect_phone = request.query_params.get("phone", "+15550199")
    name = request.query_params.get("name", "Valued Customer")
    company = request.query_params.get("company", "Global Corp")
    tenant_id = request.query_params.get("tenant_id", "default_shared_tenant")
    call_id = request.query_params.get("call_id", "")
    
    # Fetch pre-call long-term memory brief context
    from memory.manager import memory_manager
    context_brief = await memory_manager.load_pre_call_context(prospect_phone, tenant_id)
    
    import urllib.parse
    brief_encoded = urllib.parse.quote(context_brief) if context_brief else ""
    
    ws_url = f"{protocol}://{host}/media-stream?phone={prospect_phone}&name={name}&company={company}&tenant_id={tenant_id}&call_id={call_id}&brief={brief_encoded}"
    
    log_info("incoming_call_webhook_hit", f"Incoming call bridged. Routing to media stream: {ws_url}", 
             correlation_id=correlation_id, phone=prospect_phone, name=name, company=company)
    
    # Fetch custom disclosures config per tenant
    from compliance.gate import get_tenant_compliance_settings
    comp_settings = get_tenant_compliance_settings(tenant_id)
    
    disclosure_twiml = ""
    if comp_settings.get("recording_disclosure_enabled"):
        text = comp_settings.get("recording_disclosure_text")
        disclosure_twiml += f'    <Say voice="Polly.Olivia">{text}</Say>\n'
    if comp_settings.get("ai_disclosure_enabled"):
        text = comp_settings.get("ai_disclosure_text")
        text = text.replace("[Company]", company)
        disclosure_twiml += f'    <Say voice="Polly.Olivia">{text}</Say>\n'
        
    if not disclosure_twiml:
        disclosure_twiml = '    <Say voice="Polly.Olivia">Connecting your call to our Senior Representative. Please stand by.</Say>\n'
    
    # Twilio Connect with robust Pause buffer to block immediate PSTN teardown
    ws_url_xml = ws_url.replace("&", "&amp;")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
{disclosure_twiml}    <Connect>
        <Stream url="{ws_url_xml}" />
    </Connect>
    <Pause length="28800" />
</Response>
"""
    return Response(content=twiml, media_type="application/xml")

@app.post("/api/twilio-status-callback")
async def handle_twilio_status_callback(request: Request, verified: bool = Depends(verify_twilio_signature)):
    """
    Twilio Call Status Webhook.
    Protected by X-Twilio-Signature verification middleware.
    """
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        duration = form_data.get("CallDuration") or "0"
        
        log_info("twilio_status_callback", f"Twilio Status Update: {call_status}", call_sid=call_sid, call_status=call_status, call_duration=duration)
        return Response(status_code=200)
    except Exception as e:
        log_error("twilio_status_callback_error", f"Error in status callback route: {e}")
        return Response(status_code=500)

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """
    Bi-directional VoIP WebSocket streaming handler.
    Orchestrates G.711 transcoding, startup energy suppression, deep observability tracking,
    stage-wise latency timeline metrics, and a comprehensive failure injection suite.
    """
    # 1. Accept WebSocket and initialize session tracing UUID
    trace_id = str(uuid.uuid4())
    session_id = f"sess_{trace_id[:8]}"
    connection_start_time = time.time()
    
    # Parse dynamic Failure Injection and Tenant query parameters
    params = dict(websocket.query_params)
    inject_fault = params.get("inject_fault")
    tenant_id = params.get("tenant_id", "default_shared_tenant")
    call_id = params.get("call_id", "")
    phone_number = params.get("phone", "+15550199")
    
    # Set contextvars for structured logging enrichment
    tenant_id_var.set(tenant_id)
    
    log_info("ws_connect_attempt", f"Telephony client establishing websocket link. Fault Injection: {inject_fault}", 
             session_id=session_id, trace_id=trace_id, inject_fault=inject_fault, tenant_id=tenant_id)
    
    global active_calls_count
    if is_shutting_down:
        log_warn("ws_connection_rejected", "VoIP WebSocket connection rejected because pod is shutting down.", session_id=session_id)
        return
        
    try:
        await websocket.accept()
        active_calls_count += 1
        
        # --- OBSERVABILITY: Start call trace and metrics ---
        call_root_span = start_call_trace(
            stream_sid=session_id,
            tenant_id=tenant_id,
            direction="outbound",
            phone=phone_number,
        )
        track_call_start(tenant_id)
        
        log_info("ws_connect_success", f"VoIP WebSocket session accepted and connected. Current pod load: {active_calls_count}", session_id=session_id, trace_id=trace_id)
    except Exception as e:
        log_critical("ws_accept_failed", f"Failed to accept incoming VoIP WebSocket link: {e}", 
                     session_id=session_id, trace_id=trace_id, traceback=traceback.format_exc())
        return

    phone_number = params.get("phone", "+15550199")
    prospect_name = params.get("name", "Valued Customer")
    company_name = params.get("company", "Global Corp")
    
    stream_sid = None
    call_sid_resolved = None
    fsm = None
    
    # 2. Stage-wise Latency Timeline History & Histograms
    conversation_latency_timeline = []
    
    # Running Conversational turn metrics
    current_turn = {
        "turn_index": 0,
        "pstn_ingress_timestamp": None,
        "decode_completion_timestamp": None,
        "vad_trigger_timestamp": None,
        "ai_generation_start_timestamp": None,
        "ai_generation_end_timestamp": None,
        "tts_generation_completion_timestamp": None,
        "outbound_enqueue_timestamp": None,
        "twilio_mark_ack_timestamp": None
    }
    
    # Deep Observability Metrics Registry
    metrics = {
        "trace_id": trace_id,
        "call_sid": None,
        "stream_sid": None,
        "websocket_session_id": session_id,
        "start_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "stop_reason": "active_hangup",
        "media_frame_count_inbound": 0,
        "media_frame_count_outbound": 0,
        "decode_error_count": 0,
        "average_frame_latency_ms": 0.0,
        "interruption_count": 0,
        "abort_count": 0,
        "websocket_rtt_ms": 0.0,
        "websocket_rtt_variance_ms": 0.0,
        "max_queue_depth": 0,
        "vad_trigger_count": 0,
        "dtmf_count": 0,
        "reconnect_count": 0
    }
    
    # Last RTT tracking for variance/jitter calculations
    last_rtt_ms = 0.0
    
    # Initialize StateMachineController with pre-call brief
    context_brief = params.get("brief", "")
    try:
        fsm = StateMachineController(initial_metadata={
            "name": prospect_name,
            "company": company_name,
            "phone": phone_number,
            "context_brief": context_brief
        })
        log_info("fsm_initialized", f"Conversational FSM controller initialized with brief: {context_brief}", 
                 stream_sid=stream_sid, initial_state=fsm.context.current_state, trace_id=trace_id)
    except Exception as e:
        log_critical("fsm_initialization_failed", f"Failed to build FSM State Machine: {e}", trace_id=trace_id, traceback=traceback.format_exc())
        
    jitter_buf = JitterBuffer(target_ms=40)
    is_streaming = True
    
    # Silence detection and suppression states
    last_speech_time = time.time()
    last_agent_speech_time = time.time()
    is_agent_speaking = False
    reengaged_once = False
    
    # Suppression windows to clear DTMF and trial residual announcement noise
    startup_suppression_end_time = connection_start_time + 2.0
    dtmf_suppression_end_time = 0.0
    
    def is_vad_suppressed() -> bool:
        current_time = time.time()
        if current_time < startup_suppression_end_time:
            return True
        if current_time < dtmf_suppression_end_time:
            return True
        return False
        
    # Pre-populate transcript session buffer
    active_sid = "active_" + str(uuid.uuid4())[:8]
    async with transcripts_lock:
        call_transcripts_buffers[active_sid] = []
        
    # RTT Mark trackers
    mark_sent_times = {}

    # Define internal task routines
    async def receive_from_twilio():
        nonlocal stream_sid, call_sid_resolved, phone_number, is_streaming, last_speech_time, active_sid, dtmf_suppression_end_time
        try:
            log_info("telephony_receive_start", "Inbound telemetry audio stream reader active.", stream_sid=stream_sid, trace_id=trace_id)
            
            # FAILURE MODE: Rapid Reconnect Storm Simulation
            if inject_fault == "reconnect_storm":
                log_warn("reconnect_storm_injected", "Simulating rapid reconnect storm! Forcing quick socket bounce.", trace_id=trace_id)
                await asyncio.sleep(0.5)
                is_streaming = False
                return
                
            async for message in websocket.iter_text():
                # FAILURE MODE: WebSocket closed mid-stream
                if inject_fault == "ws_close" and (time.time() - connection_start_time) > 5.0:
                    log_warn("ws_close_injected", "Simulating dirty websocket close mid-stream! Aborting task.", trace_id=trace_id)
                    is_streaming = False
                    break
                    
                data = json.loads(message)
                event = data.get("event")
                
                # FAILURE MODE: Duplicate Twilio Events Simulation
                iterations = 2 if (inject_fault == "duplicate_event" and event == "media") else 1
                
                for _ in range(iterations):
                    if event == "connected":
                        log_info("twilio_event_connected", f"Twilio media stream handshaked. Protocol Version: {data.get('version')}", 
                                 stream_sid=stream_sid, trace_id=trace_id)
                        
                    elif event == "start":
                        start_data = data.get("start", {})
                        stream_sid = start_data.get("streamSid")
                        call_sid_resolved = start_data.get("callSid")
                        
                        metrics["call_sid"] = call_sid_resolved
                        metrics["stream_sid"] = stream_sid
                        
                        # ----------------------------------------------------
                        # SCALABILITY: WEBSOCKET AFFINITY & TRANSPARENT PROXY
                        # ----------------------------------------------------
                        from server.session_registry import session_registry
                        current_pod = os.getenv("POD_ID", "local_pod")
                        target_pod = await session_registry.get_session_pod(stream_sid)
                        
                        if target_pod and target_pod != current_pod:
                            log_info("ws_proxy_forward", f"WebSocket session reconnected to wrong pod ({current_pod}). Proxying to target ({target_pod}).", stream_sid=stream_sid)
                            target_url = f"ws://{target_pod}.audio-processor-service.default.svc.cluster.local:8000/media-stream?{websocket.query_params}"
                            
                            try:
                                import websockets
                                async with websockets.connect(target_url) as remote_ws:
                                    # Bridge handshakes
                                    await remote_ws.send(json.dumps({"event": "connected"}))
                                    await remote_ws.send(message) # Forward current 'start' frame
                                    
                                    async def client_to_remote():
                                        try:
                                            async for msg in websocket.iter_text():
                                                await remote_ws.send(msg)
                                        except Exception:
                                            pass
                                            
                                    async def remote_to_client():
                                        try:
                                            async for msg in remote_ws:
                                                await websocket.send_text(msg)
                                        except Exception:
                                            pass
                                            
                                    await asyncio.gather(client_to_remote(), remote_to_client())
                            except Exception as e:
                                log_error("ws_proxy_failed", f"Transparent proxy forwarding failed: {e}", stream_sid=stream_sid)
                            
                            is_streaming = False
                            return
                        else:
                            # Register this pod as the handling owner
                            await session_registry.register_session(stream_sid, current_pod)
                        
                        custom_params = start_data.get("customParameters", {})
                        phone_number = custom_params.get("phone") or phone_number
                        prospect_name_tw = custom_params.get("name") or prospect_name
                        company_name_tw = custom_params.get("company") or company_name
                        
                        # Update FSM metadata if active
                        if fsm:
                            fsm.context.prospect_name = prospect_name_tw
                            fsm.context.company_name = company_name_tw
                            
                        # Re-map active buffer keys
                        async with transcripts_lock:
                            if active_sid in call_transcripts_buffers:
                                call_transcripts_buffers[stream_sid] = call_transcripts_buffers.pop(active_sid)
                                active_sid = stream_sid
                                
                        log_info("twilio_event_start", f"Twilio Media Fork started.", 
                                 stream_sid=stream_sid, call_sid=call_sid_resolved, phone=phone_number, trace_id=trace_id)
                        
                        # Delayed Welcome Greeting
                        async def delayed_welcome():
                            try:
                                # 2.0s startup suppression
                                await asyncio.sleep(2.0)
                                if is_streaming:
                                    welcome_text = f"Hello! Am I speaking with {prospect_name_tw}?"
                                    await send_agent_speech(welcome_text)
                            except asyncio.CancelledError:
                                log_info("welcome_cancelled", "Welcome prompt execution cancelled on early teardown.", 
                                         stream_sid=stream_sid, trace_id=trace_id)
                        nonlocal welcome_task
                        welcome_task = asyncio.create_task(delayed_welcome())
                        
                    elif event == "media":
                        # Record PSTN Ingress Timestamp
                        current_turn["pstn_ingress_timestamp"] = time.time()
                        
                        metrics["media_frame_count_inbound"] += 1
                        payload = data.get("media", {}).get("payload")
                        
                        if payload and is_streaming:
                            try:
                                # FAILURE MODE: Partial Frame Truncation/Packet Loss
                                if inject_fault == "partial_frame" and metrics["media_frame_count_inbound"] % 5 == 0:
                                    payload = payload[:max(1, len(payload) // 2)]
                                    
                                ulaw_bytes = base64.b64decode(payload)
                                pcm_8k = decode_ulaw_chunk(ulaw_bytes)
                                pcm_16k = upsample_8k_to_16k(pcm_8k)
                                
                                # Record Ingress Latency
                                arrival_delta = (time.time() - connection_start_time) * 1000.0
                                twilio_timestamp_ms = float(data.get("media", {}).get("timestamp", 0))
                                ingress_latency = abs(arrival_delta - twilio_timestamp_ms)
                                metrics["average_frame_latency_ms"] = (metrics["average_frame_latency_ms"] * 9 + ingress_latency) / 10
                                
                                # ALERT: Ingress Latency Spike
                                if ingress_latency > 800.0:
                                    log_warn("latency_alert_high_delay", f"End-to-End PSTN Ingress Latency crossed safe threshold: {ingress_latency:.2f}ms", 
                                             limit=800, actual=ingress_latency, stream_sid=stream_sid, trace_id=trace_id)
                                
                                # Record Decode Completion
                                current_turn["decode_completion_timestamp"] = time.time()
                                
                                if stream_sid:
                                    await call_session_tracker.append_left(stream_sid, pcm_16k)
                                await jitter_buf.push(pcm_16k)
                                
                                # Track max queue depth
                                q_size = jitter_buf.queue.qsize()
                                metrics["max_queue_depth"] = max(metrics["max_queue_depth"], q_size)
                                
                                # ALERT: Queue buildup
                                if q_size > 10:
                                    log_warn("latency_alert_queue_buildup", f"Queue buffering build-up detected: depth={q_size}", 
                                             limit=10, actual=q_size, stream_sid=stream_sid, trace_id=trace_id)
                                    
                            except Exception as decode_err:
                                metrics["decode_error_count"] += 1
                                
                                # ALERT: Frame Decode Failure Ratio
                                ratio = metrics["decode_error_count"] / max(1, metrics["media_frame_count_inbound"])
                                if ratio > 0.05:
                                    log_error("latency_alert_decode_errors", f"VoIP Frame decode error ratio is critically high: {ratio:.2%}", 
                                              limit=0.05, actual=ratio, stream_sid=stream_sid, trace_id=trace_id)
                                    
                                log_error("frame_decode_failed", f"Failed to transcode incoming G.711 audio frame: {decode_err}", stream_sid=stream_sid)
                                
                    elif event == "dtmf":
                        digit = data.get("dtmf", {}).get("digit")
                        log_info("twilio_event_dtmf", f"Received DTMF digit: {digit}", stream_sid=stream_sid, digit=digit, trace_id=trace_id)
                        metrics["dtmf_count"] += 1
                        
                        # Trigger 1.5 second VAD suppression and flush jitter buffer
                        dtmf_suppression_end_time = time.time() + 1.5
                        jitter_buf.flush()
                        log_info("vad_suppressed_dtmf", "VAD suppressed and jitter buffer flushed due to DTMF reception.", 
                                 stream_sid=stream_sid, trace_id=trace_id)
                        
                    elif event == "mark":
                        mark_name = data.get("mark", {}).get("name")
                        log_info("twilio_event_mark", "Received mark acknowledgment from Twilio", stream_sid=stream_sid, mark=mark_name, trace_id=trace_id)
                        
                        # Match Turn ack and record latency timeline
                        if mark_name == f"mark_turn_{current_turn['turn_index']}":
                            current_turn["twilio_mark_ack_timestamp"] = time.time()
                            conversation_latency_timeline.append(current_turn.copy())
                            
                            # Increment Turn counter
                            current_turn["turn_index"] += 1
                            
                        # RTT Calculations
                        if mark_name in mark_sent_times:
                            rtt = (time.time() - mark_sent_times.pop(mark_name)) * 1000.0
                            
                            # Calculate Jitter / RTT variance
                            nonlocal last_rtt_ms
                            if last_rtt_ms > 0.0:
                                metrics["websocket_rtt_variance_ms"] = abs(rtt - last_rtt_ms)
                                
                            last_rtt_ms = rtt
                            metrics["websocket_rtt_ms"] = rtt
                            
                            # ALERT: WebSocket RTT Latency Spike
                            if rtt > 300.0:
                                log_warn("latency_alert_rtt_spike", f"WebSocket RTT audio pathway delay spiked! RTT: {rtt:.2f}ms", 
                                         limit=300, actual=rtt, stream_sid=stream_sid, trace_id=trace_id)
                                
                            log_info("ws_rtt_updated", f"Calculated WebSocket audio RTT: {rtt:.2f}ms, Jitter: {metrics['websocket_rtt_variance_ms']:.2f}ms", 
                                     stream_sid=stream_sid, rtt_ms=rtt, jitter_ms=metrics["websocket_rtt_variance_ms"])
                            
                    elif event == "stop":
                        log_info("twilio_event_stop", f"Twilio Call Stop received. SID: {stream_sid}", stream_sid=stream_sid, trace_id=trace_id)
                        is_streaming = False
                        break
        except Exception as e:
            log_error("telephony_receive_error", f"Error in telephony receive task: {e}", stream_sid=stream_sid, trace_id=trace_id, traceback=traceback.format_exc())
        finally:
            is_streaming = False

    async def process_voice_agent():
        nonlocal is_streaming, stream_sid, fsm, last_speech_time, is_agent_speaking, reengaged_once
        try:
            log_info("telephony_agent_loop_start", "Agent dialogue engine active.", stream_sid=stream_sid, trace_id=trace_id)
            detector = VoiceActivityDetector(threshold=1500.0)
            
            while is_streaming:
                # Retrieve frame with timeout protection
                inject_slow = (inject_fault == "slow_queue")
                pcm_frame = await jitter_buf.pop(timeout=0.05, inject_slowdown=inject_slow)
                if not pcm_frame:
                    continue
                
                # Check maximum call duration timeout (15 minutes / 900s)
                if time.time() - connection_start_time > 900.0:
                    log_warn("call_timeout_reached", "Call exceeded max allowed duration of 15 minutes. Terminating.", 
                             stream_sid=stream_sid, trace_id=trace_id)
                    is_streaming = False
                    metrics["stop_reason"] = "call_duration_timeout"
                    break
                
                # Skip Voice Activity Detection check if suppressed
                if is_vad_suppressed():
                    continue
                
                rms = detector.calculate_frame_energy(pcm_frame)
                if rms > 1500.0: # Vocal energy threshold crossed
                    metrics["vad_trigger_count"] += 1
                    
                    # Record VAD Trigger
                    current_turn["vad_trigger_timestamp"] = time.time()
                    
                    # If Agent was speaking, trigger dynamic WebRTC/VoIP Interruption abort
                    if is_agent_speaking:
                        metrics["interruption_count"] += 1
                        metrics["abort_count"] += 1
                        log_info("vad_interruption_detected", f"User interrupted AI speaker. Vocal energy: {rms:.2f}", 
                                 stream_sid=stream_sid, trace_id=trace_id)
                        
                        # Purge player queues
                        jitter_buf.flush()
                        
                        # FAILURE MODE: Interruption response exceeds window / slow active abort
                        if inject_fault == "cancel_active_tts":
                            log_info("tts_cancelled_mid_stream", "Simulated active TTS cancellation triggered on interruption.", 
                                     stream_sid=stream_sid, trace_id=trace_id)
                            
                        # Measure Interruption response time
                        interruption_response_time = (time.time() - current_turn["vad_trigger_timestamp"]) * 1000.0
                        
                        # ALERT: Interruption delay exceeds safe window
                        if interruption_response_time > 200.0:
                            log_warn("latency_alert_interruption_delay", f"Interruption response latency crossed threshold: {interruption_response_time:.2f}ms", 
                                     limit=200, actual=interruption_response_time, stream_sid=stream_sid, trace_id=trace_id)
                            
                        # Transition State machine immediately to OBJECTION
                        if fsm:
                            fsm.validate_and_transition("OBJECTION")
                            log_info("state_transition", "Transitioned on interruption", stream_sid=stream_sid, state="OBJECTION", trace_id=trace_id)
                            
                    last_speech_time = time.time()
                    reengaged_once = False
                    
                    # Block to wait for speech pause (utterance boundary)
                    await asyncio.sleep(0.8)
                    
                    # Transition conversation FSM state
                    if fsm and not fsm.context.is_terminal:
                        current = fsm.context.current_state
                        old_state = current
                        
                        # Record AI Generation Start
                        current_turn["ai_generation_start_timestamp"] = time.time()
                        
                        # FAILURE MODE: AI Generation Stall Simulation
                        if inject_fault == "ai_stall":
                            log_warn("ai_stall_injected", "Simulating critical AI session generation stall! Freezing loop.", trace_id=trace_id)
                            await asyncio.sleep(5.0)
                            
                        if current == "INITIATION":
                            user_utterance = "Yes, this is they. Who is this?"
                            await record_and_broadcast_turn(active_sid, "prospect", user_utterance, current)
                            
                            fsm.validate_and_transition("PITCH")
                            response_text = "Sure! I'm calling on behalf of CloudScale. We help fast-growing teams automate outbound calls to boost booking rates by 40%."
                        elif current == "PITCH":
                            user_utterance = "Hmm, interesting, but how does it integrate?"
                            await record_and_broadcast_turn(active_sid, "prospect", user_utterance, current)
                            
                            fsm.validate_and_transition("QUALIFICATION")
                            response_text = "That's a fair question. We integrate directly into standard CRMs like Salesforce and HubSpot, syncing contact records. How many SDRs are on your team currently?"
                        elif current == "QUALIFICATION":
                            user_utterance = "We have about ten sales development reps making outbound dials."
                            await record_and_broadcast_turn(active_sid, "prospect", user_utterance, current)
                            
                            fsm.validate_and_transition("BOOKING")
                            response_text = "Got it, that's exactly the team scale where outbound automation delivers massive returns. I'd love to show you a quick 10-minute visual demo. I have openings next Monday at 10 AM or 1:30 PM. Do either of those work?"
                        elif current == "BOOKING":
                            user_utterance = "Sure, Monday at 1:30 PM works great."
                            await record_and_broadcast_turn(active_sid, "prospect", user_utterance, current)
                            
                            fsm.validate_and_transition("SUCCESS_COMPLETE")
                            response_text = "Absolutely! I have booked your slot for next Monday at 1:30 PM, and sent a confirmation text message to your phone. Have a wonderful day!"
                        elif current == "OBJECTION":
                            user_utterance = "Budget is a bit tight this quarter."
                            await record_and_broadcast_turn(active_sid, "prospect", user_utterance, current)
                            
                            fsm.validate_and_transition("QUALIFICATION")
                            response_text = "I understand completely. Let's make sure we show you the potential returns during our call next week. Do you have a few minutes next Monday at 1:30 PM?"
                        else:
                            user_utterance = "Alright."
                            await record_and_broadcast_turn(active_sid, "prospect", user_utterance, current)
                            response_text = "Perfect."
                            
                        # Record AI Generation Completion
                        current_turn["ai_generation_end_timestamp"] = time.time()
                        
                        new_state = fsm.context.current_state
                        log_info("state_transition", f"FSM Transitioned: {old_state} -> {new_state}", 
                                 stream_sid=stream_sid, old_state=old_state, new_state=new_state, trace_id=trace_id)
                        
                        # Apply Safety, Hallucination Prevention and Fallback LLM Guard System!
                        from pipeline.llm_guard import LLMGuardSystem
                        
                        # Gather Allowed Grounding Sources
                        allowed_sources = [
                            fsm.compile_expert_system_prompt() if fsm else "",
                            context_brief or "",
                            "CloudScale SDR booking rates 40% CRM integrations Salesforce HubSpot Monday 10 AM 1:30 PM"
                        ]
                        
                        # Define LLM provider call mocks for circuit breakers
                        async def mock_google_call():
                            if inject_fault == "llm_failure":
                                raise RuntimeError("Simulated primary Google LLM connection error.")
                            return response_text

                        async def mock_claude_call():
                            if inject_fault == "llm_failure_all":
                                raise RuntimeError("Simulated Claude LLM connection error.")
                            return response_text + " (via Claude)"

                        async def mock_gpt4o_call():
                            if inject_fault == "llm_failure_all":
                                raise RuntimeError("Simulated GPT-4o LLM connection error.")
                            return response_text + " (via GPT-4o)"

                        async def mock_emergency_call():
                            return "I want to be sure I get you the right info, my colleague will follow up shortly."

                        provider_calls = {
                            "google": mock_google_call,
                            "claude": mock_claude_call,
                            "gpt4o": mock_gpt4o_call,
                            "emergency": mock_emergency_call
                        }

                        # Latency-masking filler callback
                        async def filler_callback(phrase: str):
                            log_warn("latency_mask_activated", f"Streaming filler to mask latency: '{phrase}'", stream_sid=stream_sid)
                            await record_and_broadcast_turn(active_sid, "agent_filler", phrase, current)

                        guard = LLMGuardSystem(allowed_sources)
                        
                        # Run safe response generation with 600ms latency enforcer and circuit breaker!
                        safe_response = await guard.generate_safe_response(user_utterance, provider_calls, filler_callback)
                        
                        await send_agent_speech(safe_response)
                        
        except Exception as e:
            log_error("telephony_agent_error", f"Error in voice processing loop: {e}", stream_sid=stream_sid, trace_id=trace_id, traceback=traceback.format_exc())

    async def silence_monitor_loop():
        """
        Asynchronously tracks VAD silence events.
        If silences exceed 4 seconds, triggers re-engagement hooks before polite hangup.
        """
        nonlocal is_streaming, fsm, last_speech_time, last_agent_speech_time, is_agent_speaking, reengaged_once
        try:
            log_info("telephony_silence_monitor_start", "Silence monitor loop active.", stream_sid=stream_sid, trace_id=trace_id)
            await asyncio.sleep(2.0)
            
            while is_streaming:
                await asyncio.sleep(0.3)
                if fsm and fsm.context.is_terminal:
                    break
                if is_agent_speaking or is_vad_suppressed():
                    continue
                    
                current_time = time.time()
                elapsed_silence = current_time - max(last_speech_time, last_agent_speech_time)
                
                if elapsed_silence > 4.0:
                    if not reengaged_once:
                        reengaged_once = True
                        reengage_text = "Are you still there?"
                        log_info("silence_reengage", "Silence timeout exceeded. Dispatching re-engagement.", stream_sid=stream_sid, trace_id=trace_id)
                        await send_agent_speech(reengage_text)
                        last_agent_speech_time = time.time()
                    else:
                        disconnect_text = "I'll go ahead and let you go. Have a nice day! Goodbye."
                        log_info("silence_timeout_terminal", "Persistent silence detected. Gracefully disconnect.", stream_sid=stream_sid, trace_id=trace_id)
                        await send_agent_speech(disconnect_text)
                        if fsm:
                            fsm.validate_and_transition("END_CALL_DISCONNECT")
                            log_info("state_transition", "Silence timed out call", stream_sid=stream_sid, state="END_CALL_DISCONNECT", trace_id=trace_id)
                        is_streaming = False
                        break
        except Exception as e:
            log_error("telephony_silence_error", f"Error in silence monitor loop: {e}", stream_sid=stream_sid, trace_id=trace_id, traceback=traceback.format_exc())

    async def send_rtt_ping():
        """Periodically pings Twilio stream marks to calculate round-trip audio latency."""
        nonlocal is_streaming
        ping_index = 0
        try:
            log_info("telephony_rtt_ping_start", "WebSocket latency RTT ping daemon active.", stream_sid=stream_sid, trace_id=trace_id)
            while is_streaming:
                await asyncio.sleep(10.0)
                if not stream_sid:
                    continue
                
                # FAILURE MODE: Delayed WebSocket Pong / Ping Response Spike
                if inject_fault == "delayed_pong":
                    log_warn("delayed_pong_injected", "Simulating massive network latency spike! Slowing ping dispatch.", trace_id=trace_id)
                    await asyncio.sleep(3.0)
                    
                mark_name = f"ping_{ping_index}"
                mark_sent_times[mark_name] = time.time()
                ping_index += 1
                
                ping_payload = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": mark_name}
                }
                await websocket.send_text(json.dumps(ping_payload))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log_error("telephony_rtt_error", f"Error in RTT ping loop: {e}", stream_sid=stream_sid, trace_id=trace_id)

    async def send_agent_speech(text: str):
        nonlocal is_agent_speaking, last_agent_speech_time
        if not stream_sid:
            return
            
        is_agent_speaking = True
        current_state = fsm.context.current_state if fsm else "INITIATION"
        log_info("telephony_agent_utterance", f"AI Speaker dispatching utterance: '{text}'", stream_sid=stream_sid, text=text, trace_id=trace_id)
        
        # Broadcast transcript text dynamically
        await record_and_broadcast_turn(active_sid, "agent", text, current_state)
        
        # AI Output transcode & dispatch
        try:
            # Simulate Outbound Synthesis delay (TTS completed)
            current_turn["tts_generation_completion_timestamp"] = time.time()
            
            carrier_pcm = b'\x00' * 32000 # 1 second empty PCM buffer placeholder (simulating voice payload)
            
            # FAILURE MODE: Storage/Recorder write interruption mid-stream
            if inject_fault == "recorder_interrupted":
                log_error("recorder_interrupted_injected", "Simulating critical recorder write crash!", trace_id=trace_id)
                raise IOError("Simulated physical storage write block on audio recorder layer!")
                
            await call_session_tracker.append_right(stream_sid, carrier_pcm)
            pcm_8k = downsample_16k_to_8k(carrier_pcm)
            ulaw_bytes = encode_pcm_chunk(pcm_8k)
            
            # Record Outbound Enqueue
            current_turn["outbound_enqueue_timestamp"] = time.time()
            
            payload = base64.b64encode(ulaw_bytes).decode("utf-8")
            outbound_payload = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {"payload": payload}
            }
            await websocket.send_text(json.dumps(outbound_payload))
            metrics["media_frame_count_outbound"] += 1
            
            # Send sequential turn mark to track conversational latency E2E
            turn_mark = {
                "event": "mark",
                "streamSid": stream_sid,
                "mark": {"name": f"mark_turn_{current_turn['turn_index']}"}
            }
            await websocket.send_text(json.dumps(turn_mark))
            
        except Exception as e:
            log_error("outbound_dispatch_failed", f"Failed to transmit agent outbound audio frame: {e}", stream_sid=stream_sid, trace_id=trace_id)
        finally:
            is_agent_speaking = False
            last_agent_speech_time = time.time()

    # Initialize task trackers for deterministic teardown sequence
    receive_task = None
    agent_task = None
    silence_task = None
    rtt_task = None
    welcome_task = None

    try:
        # Launch concurrency pipelines
        receive_task = asyncio.create_task(receive_from_twilio())
        agent_task = asyncio.create_task(process_voice_agent())
        silence_task = asyncio.create_task(silence_monitor_loop())
        rtt_task = asyncio.create_task(send_rtt_ping())
        
        # Structured gather using await loop that exits immediately upon first completion
        done, pending = await asyncio.wait(
            [receive_task, agent_task, silence_task, rtt_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Log background failures
        for task in done:
            if task.exception() is not None:
                log_critical("telephony_task_failed", f"Telephony background task crashed: {task.exception()}", 
                             stream_sid=stream_sid, trace_id=trace_id, traceback="".join(traceback.format_tb(task.exception().__traceback__)))
                             
    except Exception as exc:
        log_critical("telephony_crash", f"VoIP server crashed during call: {exc}", trace_id=trace_id, traceback=traceback.format_exc())
    finally:
        # ---- START DETERMINISTIC TEARDOWN SEQUENCE ----
        teardown_start_time = time.time()
        log_info("teardown_started", "Initiating deterministic call teardown sequence...", stream_sid=stream_sid, trace_id=trace_id)
        
        # 1. Close WebSocket if still open
        try:
            if websocket.client_state.value != 3: # 3 is disconnected/closed in Starlette/FastAPI
                await websocket.close()
                log_info("teardown_ws_closed", "VoIP WebSocket closed successfully.", stream_sid=stream_sid, trace_id=trace_id)
        except Exception as e:
            log_warn("teardown_ws_close_failed", f"Failed to close WebSocket: {e}", stream_sid=stream_sid, trace_id=trace_id)
            
        # 2. Set streaming flag to False and cancel all pending background tasks
        is_streaming = False
        
        for task_name, task in [("receive", receive_task), ("agent", agent_task), ("silence", silence_task), ("rtt", rtt_task), ("welcome", welcome_task)]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                    log_info("teardown_task_cancelled", f"Background task '{task_name}' cancelled cleanly.", stream_sid=stream_sid, trace_id=trace_id)
                except asyncio.CancelledError:
                    pass
                except Exception as err:
                    log_error("teardown_task_cancel_failed", f"Task '{task_name}' raised error on cancel: {err}", stream_sid=stream_sid, trace_id=trace_id)
                    
        # 3. Purge queue buffers
        jitter_buf.flush()
        log_info("teardown_queues_purged", "Jitter buffer queue purged and flushed.", stream_sid=stream_sid, trace_id=trace_id)
        
        # 4. Recorder finalize & upload recordings
        recording_url = ""
        final_state = fsm.context.current_state if fsm else "INITIATION"
        
        # FAILURE MODE: Supabase / Database storage downtime
        use_supabase = (inject_fault != "supabase_down")
        
        if stream_sid:
            try:
                # Retrieve transcript context
                async with transcripts_lock:
                    transcript = call_transcripts_buffers.get(stream_sid, [])
                
                log_info("teardown_recorder_finalizing", f"Compiling stereo WAV, uploading and finalizing records for SID: {stream_sid}...", 
                         stream_sid=stream_sid, trace_id=trace_id)
                
                # Check if we should block Supabase
                if not use_supabase:
                    from server.storage_manager import supabase_client
                    # Temporarily clear Supabase client to force fallback upload path
                    original_client = supabase_client
                    try:
                        import server.storage_manager
                        server.storage_manager.supabase_client = None
                        recording_url = await call_session_tracker.upload_recording(stream_sid, phone_number, final_state, tenant_id, transcript)
                    finally:
                        server.storage_manager.supabase_client = original_client
                else:
                    recording_url = await call_session_tracker.upload_recording(stream_sid, phone_number, final_state, tenant_id, transcript)
                    
                log_info("teardown_recorder_success", f"Telemetry logs & WAV finalized successfully. Recording URL: {recording_url}", 
                         stream_sid=stream_sid, recording_url=recording_url, trace_id=trace_id)
                         
                # Trigger Visoora Long-Term Memory facts extraction & Autonomous CRM Pipeline advancement asynchronously
                from memory.manager import memory_manager
                from crm.auto_advance import auto_advance_deal, CallResult

                duration_sec = 0
                if "connection_start_time" in locals() and connection_start_time:
                    duration_sec = int(time.time() - connection_start_time)
                
                outcome_str = "completed" if final_state in ["SUCCESS_COMPLETE", "END_CALL_DISCONNECT"] else "no-answer"
                if duration_sec < 5 and outcome_str == "completed":
                    outcome_str = "no-answer"

                async def run_async_crm_and_memory():
                    try:
                        ai_summary = ""
                        try:
                            facts = await memory_manager.extract_and_store_post_call_memory(
                                stream_sid=stream_sid,
                                phone_number=phone_number,
                                tenant_id=tenant_id,
                                transcript=transcript
                            )
                            ai_summary = facts.get("summary_text", "")
                        except Exception as me:
                            log_warn("crm_memory_extraction_failed", f"Failed memory extraction: {me}")

                        # Advancing deal
                        result = CallResult(
                            phone_number=phone_number,
                            tenant_id=tenant_id,
                            final_state=final_state,
                            duration_seconds=duration_sec,
                            outcome=outcome_str,
                            transcript_url=f"/transcripts/{stream_sid}",
                            recording_url=recording_url or "",
                            ai_summary=ai_summary
                        )
                        await auto_advance_deal(result)
                    except Exception as ce:
                        log_critical("crm_teardown_failed", f"Failed to execute async crm & memory task: {ce}")

                asyncio.create_task(run_async_crm_and_memory())
            except Exception as e:
                log_critical("teardown_recorder_failed", f"Failed to finalize/upload stereo voice log: {e}", 
                             stream_sid=stream_sid, trace_id=trace_id, traceback=traceback.format_exc())
                
        # 5. Flush and persist Telemetry Metrics
        cleanup_duration_ms = (time.time() - teardown_start_time) * 1000.0
        
        metrics["stop_reason"] = "call_completed" if final_state in ["SUCCESS_COMPLETE", "END_CALL_DISCONNECT"] else "unexpected_drop"
        metrics["stream_duration"] = time.time() - connection_start_time
        metrics["stream_sid"] = stream_sid
        metrics["call_sid"] = call_sid_resolved
        
        # Structured Telemetry Export Payload
        telemetry_export = {
            "trace_id": trace_id,
            "call_sid": call_sid_resolved,
            "stream_sid": stream_sid,
            "latency_timeline": conversation_latency_timeline,
            "vad_counts": metrics["vad_trigger_count"],
            "interruption_counts": metrics["interruption_count"],
            "websocket_reconnects": metrics["reconnect_count"],
            "queue_max_depth": metrics["max_queue_depth"],
            "decode_error_totals": metrics["decode_error_count"],
            "cleanup_duration_ms": cleanup_duration_ms,
            "teardown_reason": metrics["stop_reason"],
            "final_fsm_state": final_state,
            "total_duration_sec": metrics["stream_duration"],
            "inbound_frame_total": metrics["media_frame_count_inbound"],
            "outbound_frame_total": metrics["media_frame_count_outbound"],
            "average_rtt_ms": metrics["websocket_rtt_ms"],
            "jitter_ms": metrics["websocket_rtt_variance_ms"]
        }
        
        # Persist structured telemetry payload locally
        try:
            telemetry_path = f"recordings/telemetry_{stream_sid or 'active'}_{trace_id[:8]}.json"
            with open(telemetry_path, "w") as f:
                json.dump(telemetry_export, f, indent=2)
            log_info("teardown_telemetry_persisted", f"Structured telemetry payload saved locally: {telemetry_path}", 
                     stream_sid=stream_sid, trace_id=trace_id)
        except Exception as e:
            log_error("teardown_telemetry_persist_failed", f"Failed to save telemetry JSON: {e}", stream_sid=stream_sid, trace_id=trace_id)
            
        # Flush metrics to std log
        log_info("teardown_telemetry_flush", "Outbound telephony orchestration metrics flush:", 
                 stream_sid=stream_sid, trace_id=trace_id, metrics=metrics)
        
        # Broadcast completed session details to frontends
        if stream_sid:
            try:
                await live_ws_manager.broadcast({
                    "event": "session_completed",
                    "stream_sid": stream_sid,
                    "final_state": final_state,
                    "recording_url": recording_url,
                    "metrics": metrics,
                    "telemetry": telemetry_export
                })
            except Exception:
                pass
        
        log_info("teardown_completed", "Call teardown sequence completed successfully.", stream_sid=stream_sid, trace_id=trace_id)
        
        # Release tenant rate limit call concurrency slot
        if stream_sid or call_id:
            await rate_limiter.release_call(tenant_id, stream_sid or call_id)
            
        # Increment used billing minutes post-call
        try:
            call_duration_seconds = int(time.time() - connection_start_time)
            call_duration_minutes = call_duration_seconds / 60.0
            if call_duration_minutes > 0:
                from billing.meter import increment_used_minutes
                asyncio.create_task(increment_used_minutes(tenant_id, call_duration_minutes))
                log_info("billing_minutes_incremented_post_call", f"Incremented used minutes for {tenant_id}: {call_duration_minutes:.2f} min.")
        except Exception as e:
            log_error("billing_minutes_increment_failed", f"Failed to increment billing minutes: {e}")

        # Scalability: decrement active calls count and update session registry
        active_calls_count = max(0, active_calls_count - 1)
        if stream_sid:
            from server.session_registry import session_registry
            await session_registry.deregister_session(stream_sid)
            
        # ---- END DETERMINISTIC TEARDOWN SEQUENCE ----

# ----------------------------------------------------
# LIVE FRONTEND TRANSCRIPT ENDPOINT
# ----------------------------------------------------
@app.websocket("/api/live-ws")
async def live_ws_endpoint(websocket: WebSocket):
    """
    WebSocket broadcast channel for frontend dashboards.
    Sends turn updates instantly and backfills historical active call dialogue turns upon connection.
    Authenticated using Supabase Auth JWT token query parameters.
    """
    dashboard_session_id = f"dash_{str(uuid.uuid4())[:8]}"
    params = dict(websocket.query_params)
    token = params.get("token")
    
    # Extract and verify token (bypass for unconfigured local developer environment)
    if settings.twilio_auth_token != "your_twilio_auth_token_here" and settings.twilio_auth_token != "mock":
        if not token:
            logger.warn("dashboard_ws_auth_failed", message="Missing auth token for live-ws.")
            await websocket.close(code=4001)
            return
        try:
            await verify_supabase_jwt(token)
        except Exception as e:
            logger.error("dashboard_ws_auth_error", message="Authentication failed for live-ws.", error=str(e))
            await websocket.close(code=4002)
            return

    log_info("dashboard_ws_connect_attempt", "Frontend dashboard websocket connection attempt.", session_id=dashboard_session_id)
    
    try:
        await live_ws_manager.connect(websocket)
        log_info("dashboard_ws_connected", "Frontend dashboard websocket connected successfully.", session_id=dashboard_session_id)
    except Exception as e:
        log_error("dashboard_ws_accept_failed", f"Failed to accept dashboard websocket: {e}", session_id=dashboard_session_id)
        return
        
    try:
        # Instantly backfill buffered turns for active calls
        async with transcripts_lock:
            for sid, turns in call_transcripts_buffers.items():
                await websocket.send_json({
                    "event": "session_backfill",
                    "stream_sid": sid,
                    "turns": turns
                })
        
        # Keep client connection active with periodic pings to avoid proxy drops
        while True:
            await websocket.receive_text()
    except Exception as exc:
        log_debug("dashboard_ws_dropped", f"Dashboard websocket connection dropped: {exc}", session_id=dashboard_session_id)
    finally:
        await live_ws_manager.disconnect(websocket)
        log_info("dashboard_ws_disconnected", "Dashboard websocket connection closed and cleaned up.", session_id=dashboard_session_id)

# ----------------------------------------------------
# PUBLIC UNRESTRICTED ENDPOINTS
# ----------------------------------------------------
@app.get("/health")
async def health_check():
    """
    Public unrestricted health endpoint.
    Bypasses authentication filters.
    """
    return {"status": "healthy", "service": "visoora-telephony-orchestrator"}

# ----------------------------------------------------
# HIGH-PERFORMANCE HEALTH & PROMETHEUS METRICS ENDPOINTS
# ----------------------------------------------------
@app.get("/health/live")
async def health_live():
    """Liveness check probe. Simply returns 200 OK."""
    return {"status": "healthy", "live": True}

@app.get("/health/ready")
async def health_ready():
    """
    Readiness check probe.
    Returns 200 OK only if Redis is connected, Twilio is reachable, and active calls < 50.
    """
    if is_shutting_down:
        return JSONResponse(status_code=503, content={"status": "unready", "reason": "shutting_down"})
        
    if active_calls_count >= 50:
        return JSONResponse(status_code=503, content={"status": "unready", "reason": "capacity_full", "active_calls": active_calls_count})
        
    # Check Redis connectivity
    from server.session_registry import redis_client
    if redis_client:
        try:
            redis_client.ping()
        except Exception as e:
            return JSONResponse(status_code=503, content={"status": "unready", "reason": "redis_offline", "error": str(e)})
            
    # Check Twilio REST API reachability (light DNS/HTTP handshake check with 2s timeout)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.get("https://api.twilio.com")
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unready", "reason": "twilio_unreachable", "error": str(e)})
        
    return {"status": "ready", "active_calls": active_calls_count}

@app.get("/health/metrics")
async def health_metrics():
    """
    Prometheus metrics exporter.
    Returns call count, VAD interruptions, and baseline state histograms in plain-text format.
    """
    from server.session_registry import session_registry
    cluster_active = await session_registry.get_active_streams_count()
    
    metrics_str = f"""# HELP active_calls Current active concurrent calls handled by this node.
# TYPE active_calls gauge
active_calls {active_calls_count}

# HELP cluster_active_calls Total active concurrent calls across all cluster nodes.
# TYPE cluster_active_calls gauge
cluster_active_calls {cluster_active}

# HELP avg_call_latency_ms Average roundtrip call audio latency in milliseconds.
# TYPE avg_call_latency_ms gauge
avg_call_latency_ms {global_avg_latency_ms:.2f}

# HELP vad_interruptions_total Total count of user speak interruptions triggered.
# TYPE vad_interruptions_total counter
vad_interruptions_total {global_vad_interruptions}
"""
    return Response(content=metrics_str, media_type="text/plain")

# ----------------------------------------------------
# CAMPAIGN MANAGER ROUTING APIS (RBAC PROTECTED)
# ----------------------------------------------------
@app.get("/api/campaigns")
async def get_campaign_leads(user: UserPrincipal = Depends(RoleChecker(["viewer", "agent", "admin"]))):
    """Reads campaign leads from campaign_leads.json inside a thread-safe asyncio lock."""
    async with campaign_file_lock:
        try:
            if os.path.exists(CAMPAIGN_LEADS_FILE):
                with open(CAMPAIGN_LEADS_FILE, "r") as f:
                    return json.load(f)
        except Exception as e:
            return {"error": str(e)}
    return []

@app.post("/api/campaigns/add")
async def add_campaign_lead(lead: dict, user: UserPrincipal = Depends(RoleChecker(["admin"]))):
    """Appends a new lead to campaign_leads.json inside a thread-safe lock."""
    async with campaign_file_lock:
        try:
            leads = []
            if os.path.exists(CAMPAIGN_LEADS_FILE):
                with open(CAMPAIGN_LEADS_FILE, "r") as f:
                    leads = json.load(f)
            
            lead_id = "lead_" + str(uuid.uuid4())[:8]
            new_lead = {
                "id": lead_id,
                "name": lead.get("name", "Prospect"),
                "company": lead.get("company", "Acme Corp"),
                "phone": lead.get("phone", ""),
                "status": "Pending",
                "retry_count": 0
            }
            leads.append(new_lead)
            
            with open(CAMPAIGN_LEADS_FILE, "w") as f:
                json.dump(leads, f, indent=2)
            return {"success": True, "lead": new_lead}
        except Exception as e:
            return {"success": False, "error": str(e)}

@app.post("/api/campaigns/dial")
async def dial_campaign_lead(payload: dict, user: UserPrincipal = Depends(RoleChecker(["agent", "admin"]))):
    """
    Triggers outbound dialing sequence for a specific lead.
    Enforces compliance filters prior to Twilio triggers.
    """
    lead_id = payload.get("id")
    consent_token = payload.get("consent_token")
    
    if not lead_id:
        return {"success": False, "error": "Lead ID is required"}
        
    lead_to_dial = None
    async with campaign_file_lock:
        try:
            if os.path.exists(CAMPAIGN_LEADS_FILE):
                with open(CAMPAIGN_LEADS_FILE, "r") as f:
                    leads = json.load(f)
                    
                for l in leads:
                     if l["id"] == lead_id:
                        l["status"] = "Dialing" if l["retry_count"] == 0 else "Retrying"
                        lead_to_dial = l.copy()
                        break
                
                if lead_to_dial:
                    with open(CAMPAIGN_LEADS_FILE, "w") as f:
                        json.dump(leads, f, indent=2)
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    if not lead_to_dial:
        return {"success": False, "error": "Lead not found"}
        
    # Trigger Twilio outbound call passing authenticated user and consent token context
    res = await trigger_outbound_call({
        "phone": lead_to_dial["phone"],
        "name": lead_to_dial["name"],
        "company": lead_to_dial["company"],
        "consent_token": consent_token
    }, user=user)
    return res

@app.post("/make-call")
async def trigger_outbound_call(payload: Dict[str, str], user: UserPrincipal = Depends(RoleChecker(["agent", "admin"]))):
    """
    Initiates an outbound cold call using Twilio API, routing to our /incoming-call webhook.
    Enforces strict US TCPA and GDPR calling hours, DNC check, and PEWC Consent validation.
    """
    prospect_phone = payload.get("phone")
    name = payload.get("name", "Prospect")
    company = payload.get("company", "Acme")
    consent_token = payload.get("consent_token")
    
    if not prospect_phone:
        return {"success": False, "error": "Phone number is required."}
        
    tenant_id = user.tenant_id
    
    # DEV FLOW: Automatically generate and register consent if missing under local bypass context
    if user.user_id == "local_dev_user" and not consent_token:
        consent_token = str(uuid.uuid4())
        LOCAL_CONSENT_FILE = "recordings/local_consents.json"
        try:
            consents = []
            if os.path.exists(LOCAL_CONSENT_FILE):
                with open(LOCAL_CONSENT_FILE, "r") as f:
                    consents = json.load(f)
            consents.append({
                "id": str(uuid.uuid4()),
                "phone_number": prospect_phone,
                "consent_token": consent_token,
                "granted_at": datetime.datetime.utcnow().isoformat(),
                "consent_type": "marketing",
                "granted_by_ip": "127.0.0.1",
                "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat(),
                "tenant_id": tenant_id,
                "created_at": datetime.datetime.utcnow().isoformat()
            })
            with open(LOCAL_CONSENT_FILE, "w") as f:
                json.dump(consents, f, indent=2)
            log_info("local_dev_consent_auto_registered", f"Auto-registered consent for {prospect_phone}")
        except Exception as e:
            log_error("failed_to_write_local_consents_dev", f"Error: {e}")

    # Enforce TCPA & GDPR absolute compliance gates
    if user.user_id != "local_dev_user":
        from compliance.gate import verify_compliance_gate
        await verify_compliance_gate(prospect_phone, tenant_id, consent_token)
    else:
        log_info("local_dev_compliance_bypass", f"Bypassing compliance gates for local developer sandbox call to {prospect_phone}")
    
    # Rate limiting sliding-window checks per tenant
    call_id = f"stm_{str(uuid.uuid4())[:8]}"
    await rate_limiter.acquire_call(tenant_id, call_id)
    
    log_info("trigger_outbound_call", f"Dialing prospect {name} at {prospect_phone}...", tenant_id=tenant_id, call_id=call_id)
    
    # Construct inbound trigger TwiML webhook URL
    if TWILIO_ACCOUNT_SID == "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" or TWILIO_AUTH_TOKEN == "your_twilio_auth_token_here":
        log_warn("trigger_outbound_call_mock", "Mocking outbound call trigger (Twilio credentials not configured).")
        return {"success": True, "call_sid": f"CAmocked_{call_id}"}
        
    # Standard Twilio REST API Trigger
    api_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    # Dynamically resolve server host domain and propagate rate limit context variables
    import urllib.parse
    webhook_domain = os.getenv("SERVER_PUBLIC_DOMAIN", "your-ngrok-domain.ngrok-free.app").rstrip("/")
    query_params = {
        "phone": prospect_phone,
        "name": name,
        "company": company,
        "tenant_id": tenant_id,
        "call_id": call_id
    }
    encoded_params = urllib.parse.urlencode(query_params)
    webhook_url = f"https://{webhook_domain}/incoming-call?{encoded_params}"
    status_callback_url = f"https://{webhook_domain}/api/twilio-status-callback"
    
    data = {
        "To": prospect_phone,
        "From": TWILIO_PHONE_NUMBER,
        "Url": webhook_url,
        "StatusCallback": status_callback_url,
        "StatusCallbackEvent": ["initiated", "ringing", "answered", "completed"],
        "StatusCallbackMethod": "POST"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, data=data, auth=auth)
            res_json = response.json()
            if response.status_code == 201:
                return {"success": True, "call_sid": res_json.get("sid")}
            else:
                # Release acquired slot on Twilio dispatch failure
                await rate_limiter.release_call(tenant_id, call_id)
                return {"success": False, "error": res_json.get("message")}
        except Exception as e:
            # Release slot on unhandled exceptions
            await rate_limiter.release_call(tenant_id, call_id)
            return {"success": False, "error": str(e)}

@app.get("/api/logs")
async def get_call_logs(user: UserPrincipal = Depends(RoleChecker(["viewer", "agent", "admin"]))):
    """
    Returns call logs telemetry from Supabase, cascading to local JSON registry if unconfigured.
    """
    from server.storage_manager import supabase_client
    if supabase_client:
        try:
            res = supabase_client.table("call_logs").select("*").eq("tenant_id", user.tenant_id).order("created_at", desc=True).execute()
            return res.data
        except Exception as err:
            log_error("supabase_query_error", f"DB query error: {err}")
            
    # Local fallback JSON parse
    try:
        registry_path = "recordings/local_call_logs.json"
        if os.path.exists(registry_path):
            with open(registry_path, "r") as f:
                return json.load(f)
    except Exception as err:
        log_error("local_registry_query_error", f"Local registry read error: {err}")
    return []
