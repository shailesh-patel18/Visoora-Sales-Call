import threading
import logging
import asyncio
from typing import Dict, Any, Optional
from server.storage_manager import supabase_admin_client as supabase_client

logger = logging.getLogger(__name__)

class MissionMemory:
    """
    Thread-safe, shared state memory for a specific active mission.
    Acts as a blackboard where different capabilities and agents read/write data.
    """
    def __init__(self, mission_id: str, tenant_id: str = None):
        self.mission_id = mission_id
        self.tenant_id = tenant_id
        self._state: Dict[str, Any] = {
            "website_summary": None,
            "icp_definition": None,
            "pain_points": [],
            "decision_makers": [],
            "technologies": [],
            "outreach_drafts": [],
            "metadata": {
                "current_node": None,
                "completed_nodes": [],
                "retry_count": 0,
                "execution_time_ms": 0.0,
                "planner_version": "v1.0",
                "llm_version": "unknown"
            }
        }
        self._lock = threading.Lock()

    async def load(self) -> bool:
        """Load state from DB. Returns True if found, False if new mission."""
        try:
            loop = asyncio.get_running_loop()
            def _read():
                return supabase_client.table("missions").select("*").eq("id", self.mission_id).execute()
            
            res = await loop.run_in_executor(None, _read)
            if res.data:
                db_state = res.data[0].get("memory_snapshot")
                if db_state:
                    with self._lock:
                        self._state.update(db_state)
                return True
            else:
                # Initialize new mission
                def _write():
                    supabase_client.table("missions").insert({
                        "id": self.mission_id,
                        "tenant_id": self.tenant_id,
                        "status": "pending",
                        "memory_snapshot": self._state
                    }).execute()
                await loop.run_in_executor(None, _write)
                return False
        except Exception as e:
            logger.error(f"Failed to load mission {self.mission_id}: {e}")
            return False

    def _trigger_save(self):
        """Asynchronously save current snapshot to DB."""
        snapshot = self.snapshot()
        try:
            loop = asyncio.get_running_loop()
            def _update():
                supabase_client.table("missions").update({
                    "memory_snapshot": snapshot
                }).eq("id", self.mission_id).execute()
            # Fire and forget
            loop.run_in_executor(None, _update)
        except RuntimeError:
            # If no running loop, we can't easily fire and forget async
            pass

    def set(self, key: str, value: Any):
        """Set a specific memory key directly (overwrite)."""
        with self._lock:
            self._state[key] = value
        self._trigger_save()

    def append(self, key: str, value: Any):
        """Append to a list in memory."""
        with self._lock:
            if key not in self._state or not isinstance(self._state[key], list):
                self._state[key] = []
            if isinstance(value, list):
                self._state[key].extend(value)
            else:
                self._state[key].append(value)
        self._trigger_save()

    def update_metadata(self, key: str, value: Any):
        """Update a specific metadata field."""
        with self._lock:
            if "metadata" not in self._state:
                self._state["metadata"] = {}
            self._state["metadata"][key] = value
        self._trigger_save()

    def get(self, key: str) -> Any:
        """Retrieve a specific memory key."""
        with self._lock:
            return self._state.get(key)

    def snapshot(self) -> Dict[str, Any]:
        """Get a copy of the entire memory state."""
        with self._lock:
            return dict(self._state)
