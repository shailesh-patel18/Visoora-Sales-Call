"""
Visoora Prometheus Metrics — Custom gauges, counters, and histograms

Exported at /metrics via prometheus_client ASGI middleware.
All metrics are labelled for multi-tenant segmentation.
"""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)

# ====================================================
# GAUGES — real-time snapshot values
# ====================================================
ACTIVE_CALLS = Gauge(
    "visoora_active_calls_gauge",
    "Number of currently active calls (WebSocket sessions)",
    ["tenant_id"],
)

# ====================================================
# HISTOGRAMS — latency distributions
# ====================================================
CALL_DURATION = Histogram(
    "visoora_call_duration_histogram",
    "Duration of completed calls in seconds",
    ["tenant_id", "outcome"],
    buckets=[5, 15, 30, 60, 120, 180, 300, 600, 1800],
)

LLM_LATENCY = Histogram(
    "visoora_llm_latency_histogram",
    "LLM inference latency in milliseconds",
    ["provider", "model"],
    buckets=[50, 100, 200, 400, 600, 800, 1000, 1200, 1500, 2000, 3000, 5000],
)

# ====================================================
# COUNTERS — monotonically increasing event counts
# ====================================================
FSM_TRANSITIONS = Counter(
    "visoora_fsm_transitions_counter",
    "Number of FSM state transitions",
    ["from_state", "to_state", "tenant_id"],
)

VAD_INTERRUPTIONS = Counter(
    "visoora_vad_interruptions_counter",
    "Number of VAD-triggered user interruptions during agent speech",
    ["tenant_id"],
)

COMPLIANCE_BLOCKS = Counter(
    "visoora_compliance_blocks_counter",
    "Number of calls blocked by compliance gate",
    ["reason", "tenant_id"],
)

AUDIO_DECODE_ERRORS = Counter(
    "visoora_audio_decode_errors_counter",
    "Number of G.711 audio frame decode failures",
)

RECORDING_UPLOAD_TOTAL = Counter(
    "visoora_recording_upload_total",
    "Total recording upload attempts",
    ["status"],  # "success" | "failure"
)

CALL_CONNECTION_TOTAL = Counter(
    "visoora_call_connection_total",
    "Total call connection attempts",
    ["status"],  # "success" | "failure"
)

# ====================================================
# SERVICE INFO
# ====================================================
SERVICE_INFO = Info(
    "visoora_service",
    "Visoora service build information",
)


# ====================================================
# CONVENIENCE FUNCTIONS
# ====================================================
def track_call_start(tenant_id: str):
    """Increment active calls gauge on WebSocket accept."""
    ACTIVE_CALLS.labels(tenant_id=tenant_id).inc()
    CALL_CONNECTION_TOTAL.labels(status="success").inc()


def track_call_end(tenant_id: str, duration_seconds: float, outcome: str):
    """Decrement active calls gauge and record duration on WebSocket close."""
    ACTIVE_CALLS.labels(tenant_id=tenant_id).dec()
    CALL_DURATION.labels(tenant_id=tenant_id, outcome=outcome).observe(duration_seconds)


def track_fsm_transition(from_state: str, to_state: str, tenant_id: str):
    """Record an FSM state transition."""
    FSM_TRANSITIONS.labels(
        from_state=from_state, to_state=to_state, tenant_id=tenant_id
    ).inc()


def track_llm_latency(provider: str, model: str, latency_ms: float):
    """Record LLM inference latency."""
    LLM_LATENCY.labels(provider=provider, model=model).observe(latency_ms)


def track_vad_interruption(tenant_id: str):
    """Record a VAD-triggered interruption."""
    VAD_INTERRUPTIONS.labels(tenant_id=tenant_id).inc()


def track_compliance_block(reason: str, tenant_id: str):
    """Record a compliance-gated call block."""
    COMPLIANCE_BLOCKS.labels(reason=reason, tenant_id=tenant_id).inc()


def track_decode_error():
    """Record an audio decode error."""
    AUDIO_DECODE_ERRORS.inc()


def track_recording_upload(success: bool):
    """Record a recording upload attempt."""
    RECORDING_UPLOAD_TOTAL.labels(status="success" if success else "failure").inc()


def get_metrics_response() -> tuple:
    """Returns (body_bytes, content_type) for the /metrics endpoint."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
