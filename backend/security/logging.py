"""
Visoora Structured Logging — structlog with OpenTelemetry trace correlation

Every log line is JSON with: timestamp, level, trace_id, span_id,
tenant_id, stream_sid, correlation_id, event, and relevant payload.

Log levels:
  DEBUG  — audio frames (off in production)
  INFO   — FSM transitions, call events
  WARNING — VAD anomalies, LLM fallback
  ERROR  — failed recordings, Twilio errors
  CRITICAL — compliance blocks
"""

import os
import sys
import logging
from typing import Any, Dict
from contextvars import ContextVar

import structlog

# ====================================================
# CONTEXT VARIABLES — thread-safe request scoping
# ====================================================
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="unknown")
tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="system")
stream_sid_var: ContextVar[str] = ContextVar("stream_sid", default="")


def add_correlation_and_tenant(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Injects correlation ID and tenant ID from contextvars."""
    event_dict["correlation_id"] = correlation_id_var.get()
    event_dict["tenant_id"] = tenant_id_var.get()
    return event_dict


def add_stream_sid(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Injects stream_sid from contextvars if not already present."""
    if "stream_sid" not in event_dict:
        sid = stream_sid_var.get()
        if sid:
            event_dict["stream_sid"] = sid
    return event_dict


def add_trace_context(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Injects OpenTelemetry trace_id and span_id for log-to-trace correlation."""
    try:
        from observability.tracing import get_current_trace_id, get_current_span_id
        event_dict["trace_id"] = get_current_trace_id()
        event_dict["span_id"] = get_current_span_id()
    except ImportError:
        event_dict["trace_id"] = "0" * 32
        event_dict["span_id"] = "0" * 16
    return event_dict


def configure_structlog():
    """
    Configures structlog globally with JSON output for production
    (Loki/CloudWatch/Datadog ingest) and trace context injection.

    Set LOG_LEVEL env var to control verbosity (default: INFO).
    Set LOG_FORMAT=console for pretty-printed local dev output.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json").lower()

    # Select renderer based on environment
    if log_format == "console":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.contextvars.merge_contextvars,
        add_correlation_and_tenant,
        add_stream_sid,
        add_trace_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        renderer,
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Override root Python logger to use structlog-compatible JSON output
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
        )
    )
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))


# Initialize module-level logger
logger = structlog.get_logger("visoora_security")
