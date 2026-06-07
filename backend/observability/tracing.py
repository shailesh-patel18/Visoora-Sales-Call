"""
Visoora Distributed Tracing — OpenTelemetry Instrumentation

Creates per-call traces spanning the full lifecycle:
  WebSocket open → G.711 decode → VAD → LLM call → TTS → WebSocket close

Exports to Jaeger or Grafana Tempo via OTLP.
Propagates trace context through asyncio tasks using contextvars.
"""

import os
import logging
from contextvars import ContextVar
from typing import Optional, Dict, Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import StatusCode, Status
from opentelemetry.trace.propagation import set_span_in_context
from opentelemetry.context import attach, detach, get_current

# ====================================================
# CONTEXT VARIABLES FOR TRACE PROPAGATION
# ====================================================
_current_call_span: ContextVar[Optional[trace.Span]] = ContextVar("_current_call_span", default=None)
_current_stream_sid: ContextVar[str] = ContextVar("_current_stream_sid", default="")
_current_tenant_id: ContextVar[str] = ContextVar("_current_tenant_id", default="system")

# ====================================================
# TRACER INITIALIZATION
# ====================================================
_tracer: Optional[trace.Tracer] = None


def init_tracer(
    service_name: str = "visoora-telephony",
    otlp_endpoint: Optional[str] = None,
) -> trace.Tracer:
    """
    Initializes the global OpenTelemetry TracerProvider and returns a named tracer.

    Args:
        service_name: OTEL service name for span grouping in Jaeger/Tempo.
        otlp_endpoint: OTLP gRPC endpoint (e.g., "http://tempo:4317").
                       Falls back to OTEL_EXPORTER_OTLP_ENDPOINT env var,
                       then to console export for local dev.
    """
    global _tracer
    if _tracer is not None:
        return _tracer

    endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    resource = Resource.create({
        SERVICE_NAME: service_name,
        "service.version": os.getenv("APP_VERSION", "1.0.0"),
        "deployment.environment": os.getenv("DEPLOY_ENV", "development"),
        "host.name": os.getenv("POD_ID", "local"),
    })

    provider = TracerProvider(resource=resource)

    if endpoint:
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=endpoint.startswith("http://"),
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logging.getLogger("visoora.tracing").info(
            f"OTLP trace exporter configured → {endpoint}"
        )
    else:
        # Local development: print spans to console
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logging.getLogger("visoora.tracing").info(
            "No OTLP endpoint configured — using console span exporter"
        )

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name, "1.0.0")
    return _tracer


def get_tracer() -> trace.Tracer:
    """Returns the singleton tracer, initializing lazily if needed."""
    global _tracer
    if _tracer is None:
        return init_tracer()
    return _tracer


# ====================================================
# CALL-LEVEL SPAN MANAGEMENT
# ====================================================
def start_call_trace(
    stream_sid: str,
    tenant_id: str,
    direction: str = "outbound",
    phone: str = "",
    extra_attrs: Optional[Dict[str, Any]] = None,
) -> trace.Span:
    """
    Opens the root span for a call lifecycle.
    Must be closed with end_call_trace() when the WebSocket disconnects.

    Returns the root span so child spans can reference it.
    """
    tracer = get_tracer()
    span = tracer.start_span(
        name=f"call.lifecycle.{direction}",
        attributes={
            "visoora.stream_sid": stream_sid,
            "visoora.tenant_id": tenant_id,
            "visoora.direction": direction,
            "visoora.phone": phone,
            **(extra_attrs or {}),
        },
    )

    _current_call_span.set(span)
    _current_stream_sid.set(stream_sid)
    _current_tenant_id.set(tenant_id)

    return span


def end_call_trace(
    outcome: str = "completed",
    error: Optional[Exception] = None,
):
    """Ends the root call span and clears context."""
    span = _current_call_span.get()
    if span is None:
        return

    span.set_attribute("visoora.outcome", outcome)

    if error:
        span.set_status(Status(StatusCode.ERROR, str(error)))
        span.record_exception(error)
    else:
        span.set_status(Status(StatusCode.OK))

    span.end()
    _current_call_span.set(None)


# ====================================================
# CHILD SPAN HELPERS — one per pipeline stage
# ====================================================
def span_decode(stream_sid: str, frame_count: int = 0):
    """Creates a span for G.711 → PCM decode stage."""
    tracer = get_tracer()
    parent = _current_call_span.get()
    ctx = set_span_in_context(parent) if parent else None
    return tracer.start_span(
        name="audio.g711_decode",
        context=ctx,
        attributes={
            "visoora.stream_sid": stream_sid,
            "visoora.frame_count": frame_count,
        },
    )


def span_vad(stream_sid: str, rms_energy: float, triggered: bool):
    """Creates a span for VAD analysis."""
    tracer = get_tracer()
    parent = _current_call_span.get()
    ctx = set_span_in_context(parent) if parent else None
    return tracer.start_span(
        name="audio.vad",
        context=ctx,
        attributes={
            "visoora.stream_sid": stream_sid,
            "visoora.vad_rms_energy": rms_energy,
            "visoora.vad_triggered": triggered,
        },
    )


def span_llm(
    stream_sid: str,
    provider: str,
    model: str,
    tenant_id: str = "",
    fsm_state: str = "",
):
    """Creates a span for LLM inference."""
    tracer = get_tracer()
    parent = _current_call_span.get()
    ctx = set_span_in_context(parent) if parent else None
    return tracer.start_span(
        name="ai.llm_inference",
        context=ctx,
        attributes={
            "visoora.stream_sid": stream_sid,
            "visoora.llm_provider": provider,
            "visoora.llm_model": model,
            "visoora.tenant_id": tenant_id or _current_tenant_id.get(),
            "visoora.fsm_state": fsm_state,
        },
    )


def span_tts(stream_sid: str, text_length: int = 0):
    """Creates a span for TTS synthesis."""
    tracer = get_tracer()
    parent = _current_call_span.get()
    ctx = set_span_in_context(parent) if parent else None
    return tracer.start_span(
        name="audio.tts_synthesis",
        context=ctx,
        attributes={
            "visoora.stream_sid": stream_sid,
            "visoora.tts_text_length": text_length,
        },
    )


def span_fsm_transition(
    stream_sid: str,
    from_state: str,
    to_state: str,
    tenant_id: str = "",
):
    """Creates a span for FSM state transitions."""
    tracer = get_tracer()
    parent = _current_call_span.get()
    ctx = set_span_in_context(parent) if parent else None
    span = tracer.start_span(
        name="fsm.transition",
        context=ctx,
        attributes={
            "visoora.stream_sid": stream_sid,
            "visoora.fsm_from_state": from_state,
            "visoora.fsm_to_state": to_state,
            "visoora.tenant_id": tenant_id or _current_tenant_id.get(),
        },
    )
    span.end()  # Transitions are instantaneous events
    return span


def get_current_trace_id() -> str:
    """Returns the current trace ID as hex string for log correlation."""
    span = _current_call_span.get()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return "0" * 32


def get_current_span_id() -> str:
    """Returns the current span ID as hex string for log correlation."""
    span = _current_call_span.get()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return "0" * 16
