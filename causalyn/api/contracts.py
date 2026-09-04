"""Stable API contracts shared by the FastAPI boundary, proxy hooks, and clients."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


import time
import uuid


class IntentRequest(BaseModel):
    """Payload for natural language intent synthesis."""
    intent: str = Field(min_length=1, max_length=4000)
    execution_mode: str = Field(default="shadow", pattern="^(shadow|analyze)$")


class ActionType(str, Enum):
    """Categorization of intercepted agent tool actions."""
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    SHELL_COMMAND = "shell_command"
    SHELL_EXEC = "shell_exec"
    DB_MIGRATION = "db_migration"
    HTTP_REQUEST = "http_request"
    NETWORK_EGRESS = "network_egress"


class GateDecision(str, Enum):
    """Consensus gate verdict."""
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"


class InterceptActionRequest(BaseModel):
    """Payload sent by CLI / MCP proxy hook before physical mutation."""
    session_id: str = Field(default_factory=lambda: f"sess-{int(time.time())}", description="Unique agent session identifier")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Idempotency token preventing replay attacks")
    agent_framework: str = Field("custom", description="Origin: claude_code, cursor, langgraph, custom")
    action_type: ActionType = Field(..., description="Action classification")
    target_path: Optional[str] = Field(None, description="Host target path for mutation")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Raw action arguments")
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("target_path")
    @classmethod
    def validate_target_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and "\x00" in v:
            raise ValueError("Null bytes in target_path are not allowed")
        return v



class InterceptActionResponse(BaseModel):
    """Decision returned to the agent proxy hook."""
    decision: GateDecision
    paradox_index: float
    reason: str
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    audit_hash: Optional[str] = None
    article_10_audit_id: Optional[str] = None
    unified_diffs: Dict[str, str] = Field(default_factory=dict)
