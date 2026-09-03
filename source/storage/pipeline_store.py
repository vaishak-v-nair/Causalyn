"""SQLite-backed pipeline audit storage."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class PipelineStore:
    """Persist immutable pipeline summaries with bounded SQLite access."""

    def __init__(self, path: str) -> None:
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pipelines (
                    pipeline_id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_pipelines_created_at "
                "ON pipelines(created_at DESC)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def save(self, payload: dict[str, Any]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO pipelines VALUES (?, ?, ?)",
                (
                    payload["pipeline_id"],
                    payload.get("timestamp", 0),
                    json.dumps(payload, separators=(",", ":")),
                ),
            )

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM pipelines ORDER BY created_at DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]
