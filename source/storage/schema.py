"""Schema and connection setup for the transactional audit repository."""

from __future__ import annotations

import sqlite3

SCHEMA = """
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
"""


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Create the audit tables in the caller's transaction."""
    connection.executescript(SCHEMA)
    connection.execute("PRAGMA foreign_keys = ON")
