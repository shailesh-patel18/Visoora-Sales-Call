import json
import sqlite3
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)

class TelemetryStorage(ABC):
    @abstractmethod
    def log_request(self, data: Dict[str, Any]) -> None:
        """Persist a single AI request record."""
        pass

    @abstractmethod
    def log_usage(self, tenant_id: str, feature_name: str, tokens: int, cost: float) -> None:
        """Aggregate usage for billing/analytics."""
        pass


class SupabaseStorage(TelemetryStorage):
    def __init__(self, client):
        self.client = client

    def log_request(self, data: Dict[str, Any]) -> None:
        try:
            self.client.table("ai_requests").insert(data).execute()
        except Exception as e:
            logger.error("telemetry_supabase_insert_failed", error=str(e))
            raise e

    def log_usage(self, tenant_id: str, feature_name: str, tokens: int, cost: float) -> None:
        try:
            self.client.table("ai_usage").insert({
                "tenant_id": tenant_id,
                "date": datetime.utcnow().date().isoformat(),
                "feature_name": feature_name,
                "total_requests": 1,
                "total_tokens": tokens,
                "total_cost_usd": cost
            }).execute()
        except Exception as e:
            logger.error("telemetry_supabase_usage_failed", error=str(e))


class SQLiteStorage(TelemetryStorage):
    def __init__(self, db_path: str = "recordings/local_telemetry.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_requests (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT,
                    user_id TEXT,
                    workflow_id TEXT,
                    step_id TEXT,
                    agent_id TEXT,
                    task_name TEXT,
                    provider TEXT,
                    model_name TEXT,
                    latency_ms REAL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    cost_usd REAL,
                    status TEXT,
                    error_message TEXT,
                    created_at TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT,
                    date TEXT,
                    feature_name TEXT,
                    total_requests INTEGER,
                    total_tokens INTEGER,
                    total_cost_usd REAL
                )
            ''')
            conn.commit()

    def log_request(self, data: Dict[str, Any]) -> None:
        keys = list(data.keys())
        values = [data[k] for k in keys]
        placeholders = ",".join(["?"] * len(values))
        columns = ",".join(keys)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"INSERT INTO ai_requests ({columns}) VALUES ({placeholders})", values)
                conn.commit()
        except Exception as e:
            logger.error("telemetry_sqlite_insert_failed", error=str(e))
            raise e

    def log_usage(self, tenant_id: str, feature_name: str, tokens: int, cost: float) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO ai_usage (tenant_id, date, feature_name, total_requests, total_tokens, total_cost_usd) VALUES (?, ?, ?, ?, ?, ?)",
                    (tenant_id, datetime.utcnow().date().isoformat(), feature_name, 1, tokens, cost)
                )
                conn.commit()
        except Exception as e:
            logger.error("telemetry_sqlite_usage_failed", error=str(e))


class JsonStorage(TelemetryStorage):
    def __init__(self, file_path: str = "recordings/local_ai_requests.json"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def log_request(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.file_path, "r") as f:
                records = json.load(f)
            records.append(data)
            with open(self.file_path, "w") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            logger.error("telemetry_json_insert_failed", error=str(e))
            raise e

    def log_usage(self, tenant_id: str, feature_name: str, tokens: int, cost: float) -> None:
        pass


class InMemoryStorage(TelemetryStorage):
    def __init__(self):
        self.requests: List[Dict[str, Any]] = []
        self.usage: List[Dict[str, Any]] = []

    def log_request(self, data: Dict[str, Any]) -> None:
        self.requests.append(data)

    def log_usage(self, tenant_id: str, feature_name: str, tokens: int, cost: float) -> None:
        self.usage.append({
            "tenant_id": tenant_id,
            "feature_name": feature_name,
            "tokens": tokens,
            "cost": cost,
            "date": datetime.utcnow().date().isoformat()
        })
