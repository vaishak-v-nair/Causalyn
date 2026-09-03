"""Stable response contracts for the HTTP boundary."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class ErrorBody(APIModel):
    code: str
    message: str
    fields: list[dict[str, Any]] | None = None


class ErrorResponse(APIModel):
    error: ErrorBody


class HealthResponse(APIModel):
    status: str
    service: str
    maturity: str


class StateResponse(APIModel):
    data: dict[str, Any]
    files: list[str]
    file_count: int


class PipelinesResponse(APIModel):
    pipelines: list[dict[str, Any]]


class IntentResponse(APIModel):
    pipeline_id: str
    timestamp: float
    stage: str
    stages_completed: list[str]
    error: str | None = None
    intent: dict[str, Any] | None = None
    verification: str | None = None
    commit: dict[str, Any] | None = None
    execution_mode: str = "shadow"
