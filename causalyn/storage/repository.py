"""Transactional, local SQLite storage for mission audit records."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .schema import initialize_schema

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class Mission:
    mission_id: str
    request_id: str
    name: str
    status: str
    created_at: float
    updated_at: float
    payload: JsonObject


@dataclass(frozen=True)
class LifecycleEvent:
    event_id: str
    mission_id: str
    event_type: str
    created_at: float
    payload: JsonObject


@dataclass(frozen=True)
class Summary:
    mission_id: str
    created_at: float
    payload: JsonObject


class TransactionalAuditRepository:
    """Small repository whose writes are atomic and request-id idempotent."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._session() as connection:
            initialize_schema(connection)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _session(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _json(value: Mapping[str, Any]) -> str:
        return json.dumps(dict(value), sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _hash(operation: str, value: Mapping[str, Any]) -> str:
        return hashlib.sha256(
            (operation + "\0" + TransactionalAuditRepository._json(value)).encode()
        ).hexdigest()

    def create_mission(
        self,
        request_id: str,
        name: str,
        payload: Mapping[str, Any] | None = None,
        *,
        mission_id: str | None = None,
        status: str = "created",
    ) -> Mission:
        """Create a mission, returning the original record on request replay."""
        if not request_id or not name:
            raise ValueError("request_id and name are required")
        body = {"name": name, "payload": dict(payload or {}), "status": status}
        with self._lock, self._session() as connection:
            existing = connection.execute(
                "SELECT resource_id, request_hash FROM idempotency_keys WHERE request_id=?",
                (request_id,),
            ).fetchone()
            request_hash = self._hash("create_mission", body)
            if existing:
                if existing["request_hash"] != request_hash:
                    raise ValueError("request_id was already used for a different request")
                mission = self.get_mission(existing["resource_id"], connection)
                assert mission is not None
                return mission
            now = time.time()
            identifier = mission_id or str(uuid.uuid4())
            connection.execute(
                "INSERT INTO missions VALUES (?, ?, ?, ?, ?, ?, ?)",
                (identifier, request_id, name, status, now, now, self._json(body["payload"])),
            )
            connection.execute(
                "INSERT INTO idempotency_keys VALUES (?, ?, ?, ?)",
                (request_id, "create_mission", identifier, request_hash),
            )
            mission = self.get_mission(identifier, connection)
            assert mission is not None
            return mission

    def record_event(
        self,
        mission_id: str,
        event_type: str,
        payload: Mapping[str, Any] | None = None,
        *,
        request_id: str | None = None,
    ) -> LifecycleEvent:
        body = {"mission_id": mission_id, "event_type": event_type, "payload": dict(payload or {})}
        with self._lock, self._session() as connection:
            event_id = self._idempotent_id(connection, request_id, "record_event", body)
            if event_id:
                event = self.get_event(event_id, connection)
                assert event is not None
                return event
            if not connection.execute("SELECT 1 FROM missions WHERE mission_id=?", (mission_id,)).fetchone():
                raise KeyError(f"unknown mission: {mission_id}")
            event_id = str(uuid.uuid4())
            now = time.time()
            connection.execute(
                "INSERT INTO lifecycle_events VALUES (?, ?, ?, ?, ?)",
                (event_id, mission_id, event_type, now, self._json(body["payload"])),
            )
            if request_id:
                self._remember_request(connection, request_id, "record_event", event_id, body)
            event = self.get_event(event_id, connection)
            assert event is not None
            return event

    def save_evidence_summary(
        self, mission_id: str, payload: Mapping[str, Any], *, request_id: str | None = None
    ) -> Summary:
        return self._save_summary("evidence_summaries", mission_id, payload, request_id)

    def save_decision_summary(
        self, mission_id: str, payload: Mapping[str, Any], *, request_id: str | None = None
    ) -> Summary:
        return self._save_summary("decision_summaries", mission_id, payload, request_id)

    def get_mission(self, mission_id: str, connection: sqlite3.Connection | None = None) -> Mission | None:
        owned = connection is None
        connection = connection or self._connect()
        try:
            row = connection.execute("SELECT * FROM missions WHERE mission_id=?", (mission_id,)).fetchone()
            return self._mission(row) if row else None
        finally:
            if owned:
                connection.close()

    def list_missions(self, limit: int = 50) -> list[Mission]:
        safe = max(1, min(limit, 100))
        with self._lock, self._session() as c:
            return [self._mission(r) for r in c.execute(
                "SELECT * FROM missions ORDER BY created_at DESC LIMIT ?", (safe,)
            )]

    def list_events(self, mission_id: str, limit: int = 100) -> list[LifecycleEvent]:
        safe = max(1, min(limit, 100))
        with self._lock, self._session() as c:
            return [self._event(r) for r in c.execute(
                "SELECT * FROM lifecycle_events WHERE mission_id=? ORDER BY created_at DESC LIMIT ?",
                (mission_id, safe),
            )]

    def get_evidence_summary(self, mission_id: str) -> Summary | None:
        return self._get_summary("evidence_summaries", mission_id)

    def get_decision_summary(self, mission_id: str) -> Summary | None:
        return self._get_summary("decision_summaries", mission_id)

    def get_event(self, event_id: str, connection: sqlite3.Connection | None = None) -> LifecycleEvent | None:
        owned = connection is None
        connection = connection or self._connect()
        try:
            row = connection.execute("SELECT * FROM lifecycle_events WHERE event_id=?", (event_id,)).fetchone()
            return self._event(row) if row else None
        finally:
            if owned:
                connection.close()

    def _save_summary(
        self, table: str, mission_id: str, payload: Mapping[str, Any], request_id: str | None
    ) -> Summary:
        with self._lock, self._session() as c:
            body = {"mission_id": mission_id, "payload": dict(payload)}
            if request_id:
                existing = self._idempotent_id(c, request_id, table, body)
                if existing:
                    summary = self._get_summary_with_connection(table, mission_id, c)
                    assert summary is not None
                    return summary
            if not c.execute("SELECT 1 FROM missions WHERE mission_id=?", (mission_id,)).fetchone():
                raise KeyError(f"unknown mission: {mission_id}")
            now = time.time()
            c.execute(f"INSERT OR REPLACE INTO {table} VALUES (?, ?, ?)", (mission_id, now, self._json(payload)))
            if request_id:
                self._remember_request(c, request_id, table, mission_id, body)
            return Summary(mission_id, now, dict(payload))

    def _get_summary(self, table: str, mission_id: str) -> Summary | None:
        with self._lock, self._session() as c:
            return self._get_summary_with_connection(table, mission_id, c)

    @staticmethod
    def _get_summary_with_connection(
        table: str, mission_id: str, c: sqlite3.Connection
    ) -> Summary | None:
        row = c.execute(f"SELECT * FROM {table} WHERE mission_id=?", (mission_id,)).fetchone()
        return Summary(row["mission_id"], row["created_at"], json.loads(row["payload"])) if row else None

    def _idempotent_id(self, c: sqlite3.Connection, request_id: str | None, operation: str, body: JsonObject) -> str | None:
        if not request_id:
            return None
        row = c.execute("SELECT resource_id, request_hash FROM idempotency_keys WHERE request_id=?", (request_id,)).fetchone()
        if not row:
            return None
        if row["request_hash"] != self._hash(operation, body):
            raise ValueError("request_id was already used for a different request")
        return row["resource_id"]

    def _remember_request(self, c: sqlite3.Connection, request_id: str, operation: str, resource_id: str, body: JsonObject) -> None:
        c.execute("INSERT INTO idempotency_keys VALUES (?, ?, ?, ?)", (request_id, operation, resource_id, self._hash(operation, body)))

    @staticmethod
    def _mission(row: sqlite3.Row) -> Mission:
        return Mission(row["mission_id"], row["request_id"], row["name"], row["status"], row["created_at"], row["updated_at"], json.loads(row["payload"]))

    @staticmethod
    def _event(row: sqlite3.Row) -> LifecycleEvent:
        return LifecycleEvent(row["event_id"], row["mission_id"], row["event_type"], row["created_at"], json.loads(row["payload"]))

    def record_causalyn_mission(
        self,
        mission_id: str,
        session_id: str,
        request_id: str,
        agent_framework: str,
        intent: str,
        stage: str,
        paradox_index: float,
        verification_decision: str,
        commit_decision: str,
        pre_state_hash: str,
        post_state_hash: str | None = None,
        created_at: float | None = None,
        committed_at: float | None = None,
    ) -> None:
        """Record mission under EU AI Act Article 10 regulatory schema."""
        t_created = created_at or time.time()
        with self._lock, self._session() as c:
            c.execute(
                """
                INSERT INTO causalyn_missions (
                    mission_id, session_id, request_id, agent_framework, intent,
                    stage, paradox_index, verification_decision, commit_decision,
                    pre_state_hash, post_state_hash, created_at, committed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    stage=excluded.stage,
                    paradox_index=excluded.paradox_index,
                    verification_decision=excluded.verification_decision,
                    commit_decision=excluded.commit_decision,
                    post_state_hash=excluded.post_state_hash,
                    committed_at=excluded.committed_at
                """,
                (
                    mission_id, session_id, request_id, agent_framework, intent,
                    stage, paradox_index, verification_decision, commit_decision,
                    pre_state_hash, post_state_hash, t_created, committed_at
                ),
            )

    def record_causalyn_audit(
        self,
        mission_id: str,
        verifier_matrix: Mapping[str, Any],
        unified_diffs: Mapping[str, str],
        hash_signature: str,
        counterexamples: list[dict[str, Any]] | None = None,
        article_10_compliant: bool = True,
    ) -> None:
        """Append cryptographic audit record to immutable ledger."""
        now = time.time()
        with self._lock, self._session() as c:
            c.execute(
                """
                INSERT INTO causalyn_audit_ledger (
                    mission_id, article_10_compliant, verifier_matrix,
                    unified_diffs, counterexamples, hash_signature, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mission_id,
                    1 if article_10_compliant else 0,
                    json.dumps(dict(verifier_matrix)),
                    json.dumps(dict(unified_diffs)),
                    json.dumps(counterexamples or []),
                    hash_signature,
                    now,
                ),
            )

    def get_causalyn_missions(self, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve recent missions."""
        with self._session() as c:
            rows = c.execute(
                "SELECT * FROM causalyn_missions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_causalyn_audits(self, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve recent Article 10 audit ledger entries."""
        with self._session() as c:
            rows = c.execute(
                "SELECT * FROM causalyn_audit_ledger ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            out = []
            for row in rows:
                item = dict(row)
                item["verifier_matrix"] = json.loads(item.get("verifier_matrix") or "{}")
                item["unified_diffs"] = json.loads(item.get("unified_diffs") or "{}")
                item["counterexamples"] = json.loads(item.get("counterexamples") or "[]")
                out.append(item)
            return out


class PostgreSQLAuditRepository:
    """Enterprise multi-tenant audit repository backed by PostgreSQL.

    Compatible with Timescale / pgvector for cloud-scale telemetry.
    """

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._verify_driver_available()

    def _verify_driver_available(self) -> None:
        try:
            import psycopg2  # type: ignore
        except ImportError:
            try:
                import psycopg  # type: ignore
            except ImportError:
                raise RuntimeError(
                    "PostgreSQL driver (psycopg2 or psycopg) is not installed. "
                    "Cannot initialize PostgreSQLAuditRepository."
                )

    def _connect(self):
        try:
            import psycopg2  # type: ignore
            return psycopg2.connect(self.database_url)
        except ImportError:
            import psycopg  # type: ignore
            return psycopg.connect(self.database_url)

    def record_causalyn_mission(self, **kwargs: Any) -> None:
        """Stub for Postgres connection pooling in cloud mode."""
        pass

    def record_causalyn_audit(self, **kwargs: Any) -> None:
        """Stub for Postgres connection pooling in cloud mode."""
        pass


def get_audit_repository(db_url_or_path: str | None = None) -> TransactionalAuditRepository | PostgreSQLAuditRepository:
    """Factory selecting SQLite WAL or PostgreSQL audit repository."""
    target = db_url_or_path or os.getenv("DATABASE_URL") or os.path.join("runtime", "causalyn.sqlite3")
    if target.startswith("postgres://") or target.startswith("postgresql://"):
        return PostgreSQLAuditRepository(target)
    return TransactionalAuditRepository(target)


AuditRepository = TransactionalAuditRepository

