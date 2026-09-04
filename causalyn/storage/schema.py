"""Schema and connection setup for the transactional audit repository.

Supports SQLite WAL mode for embedded zero-dependency local execution
and PostgreSQL for enterprise multi-tenant deployments under EU AI Act Article 10.
"""

from __future__ import annotations

import sqlite3
from typing import Any

SQLITE_SCHEMA = """
-- Legacy audit tables
CREATE TABLE IF NOT EXISTS missions (
    mission_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lifecycle_events (
    event_id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL REFERENCES missions(mission_id),
    event_type TEXT NOT NULL,
    created_at REAL NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lifecycle_events_mission
    ON lifecycle_events(mission_id, created_at DESC);
CREATE TABLE IF NOT EXISTS evidence_summaries (
    mission_id TEXT PRIMARY KEY REFERENCES missions(mission_id),
    created_at REAL NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decision_summaries (
    mission_id TEXT PRIMARY KEY REFERENCES missions(mission_id),
    created_at REAL NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency_keys (
    request_id TEXT PRIMARY KEY,
    operation TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    request_hash TEXT NOT NULL
);

-- EU AI Act Article 10 Enterprise Tables
CREATE TABLE IF NOT EXISTS causalyn_missions (
    mission_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    request_id TEXT NOT NULL UNIQUE,
    agent_framework TEXT NOT NULL,
    intent TEXT NOT NULL,
    stage TEXT NOT NULL,
    paradox_index REAL NOT NULL DEFAULT 0.0,
    verification_decision TEXT NOT NULL,
    commit_decision TEXT NOT NULL,
    pre_state_hash TEXT NOT NULL,
    post_state_hash TEXT,
    created_at REAL NOT NULL,
    committed_at REAL
);

CREATE TABLE IF NOT EXISTS causalyn_audit_ledger (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL REFERENCES causalyn_missions(mission_id),
    article_10_compliant INTEGER NOT NULL DEFAULT 1,
    verifier_matrix TEXT NOT NULL,
    unified_diffs TEXT NOT NULL,
    counterexamples TEXT,
    hash_signature TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_causalyn_missions_session
    ON causalyn_missions(session_id);
CREATE INDEX IF NOT EXISTS idx_causalyn_audit_mission
    ON causalyn_audit_ledger(mission_id);
"""

SCHEMA = SQLITE_SCHEMA

POSTGRES_SCHEMA = """
-- EU AI Act Article 10 Enterprise Tables (PostgreSQL)
CREATE TABLE IF NOT EXISTS causalyn_missions (
    mission_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    request_id VARCHAR(64) UNIQUE NOT NULL,
    agent_framework VARCHAR(32) NOT NULL,
    intent TEXT NOT NULL,
    stage VARCHAR(32) NOT NULL,
    paradox_index NUMERIC(6, 4) NOT NULL DEFAULT 0.0,
    verification_decision VARCHAR(16) NOT NULL,
    commit_decision VARCHAR(16) NOT NULL,
    pre_state_hash CHAR(64) NOT NULL,
    post_state_hash CHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    committed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS causalyn_audit_ledger (
    audit_id BIGSERIAL PRIMARY KEY,
    mission_id VARCHAR(64) REFERENCES causalyn_missions(mission_id),
    article_10_compliant BOOLEAN NOT NULL DEFAULT TRUE,
    verifier_matrix JSONB NOT NULL,
    unified_diffs JSONB NOT NULL,
    counterexamples JSONB,
    hash_signature CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_causalyn_missions_session
    ON causalyn_missions(session_id);
CREATE INDEX IF NOT EXISTS idx_causalyn_audit_mission
    ON causalyn_audit_ledger(mission_id);
"""


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Create the audit tables in the caller's transaction."""
    connection.executescript(SQLITE_SCHEMA)
    connection.execute("PRAGMA foreign_keys = ON")


def initialize_postgres_schema(connection: Any) -> None:
    """Create the PostgreSQL audit tables."""
    with connection.cursor() as cursor:
        cursor.execute(POSTGRES_SCHEMA)
    connection.commit()
