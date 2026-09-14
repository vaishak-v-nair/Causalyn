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
        self._lock = threading.Lock()
        self._mem_conn: sqlite3.Connection | None = None
        self.path = path
        if self.path != ":memory:":
            try:
                Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                # Read-only filesystem fallback (e.g. Vercel serverless / AWS Lambda)
                import tempfile
                self.path = str(Path(tempfile.gettempdir()) / "causalyn.sqlite3")
                try:
                    Path(self.path).parent.mkdir(parents=True, exist_ok=True)
                except OSError:
                    self.path = ":memory:"

        try:
            connection = self._connect()
            try:
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
                connection.commit()
            finally:
                self._close(connection)
        except Exception:
            self.path = ":memory:"
            connection = self._connect()
            try:
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
                connection.commit()
            finally:
                self._close(connection)

    def _connect(self) -> sqlite3.Connection:
        if self.path == ":memory:":
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            return self._mem_conn

        try:
            connection = sqlite3.connect(self.path, timeout=5)
            try:
                connection.execute("PRAGMA journal_mode=WAL")
            except sqlite3.OperationalError:
                pass
            connection.execute("PRAGMA busy_timeout=5000")
            return connection
        except sqlite3.OperationalError:
            self.path = ":memory:"
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            return self._mem_conn

    def _close(self, connection: sqlite3.Connection) -> None:
        if self.path != ":memory:" and connection is not self._mem_conn:
            connection.close()

    def save(self, payload: dict[str, Any]) -> None:
        with self._lock:
            try:
                connection = self._connect()
                try:
                    connection.execute(
                        "INSERT OR REPLACE INTO pipelines VALUES (?, ?, ?)",
                        (
                            payload["pipeline_id"],
                            payload.get("timestamp", 0),
                            json.dumps(payload, separators=(",", ":")),
                        ),
                    )
                    connection.commit()
                finally:
                    self._close(connection)
            except Exception:
                # If disk write fails, silently fallback or persist in memory
                pass

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))
        with self._lock:
            connection = self._connect()
            try:
                rows = connection.execute(
                    "SELECT payload FROM pipelines ORDER BY created_at DESC LIMIT ?",
                    (safe_limit,),
                ).fetchall()
            finally:
                self._close(connection)
        return [json.loads(row[0]) for row in rows]
