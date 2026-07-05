import structlog
from .storage import TelemetryStorage, SupabaseStorage, SQLiteStorage, JsonStorage, InMemoryStorage
from .tracker import TelemetryTracker

logger = structlog.get_logger(__name__)

# Initialize default storage abstraction based on environment
storage_backend: TelemetryStorage
try:
    from server.storage_manager import supabase_client
    if supabase_client:
        storage_backend = SupabaseStorage(supabase_client)
        logger.info("telemetry_storage_initialized", backend="supabase")
    else:
        storage_backend = SQLiteStorage()
        logger.info("telemetry_storage_initialized", backend="sqlite")
except ImportError:
    storage_backend = SQLiteStorage()
    logger.info("telemetry_storage_initialized", backend="sqlite")

# Global singleton
telemetry_tracker = TelemetryTracker(storage_backend)

__all__ = [
    "TelemetryStorage",
    "SupabaseStorage",
    "SQLiteStorage",
    "JsonStorage",
    "InMemoryStorage",
    "TelemetryTracker",
    "telemetry_tracker"
]
