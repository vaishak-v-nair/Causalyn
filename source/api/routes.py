"""FastAPI route wiring for the backend service."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException

from .contracts import IntentRequest
from .responses import HealthResponse, IntentResponse, PipelinesResponse, StateResponse
from .services import BackendService


def create_router(
    service: BackendService, serialize_context: Callable[[Any], dict[str, Any]]
) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/health", response_model=HealthResponse)
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "causalyn", "maturity": "M1_TOY_PROTOTYPE"}

    @router.get("/state", response_model=StateResponse)
    def state() -> dict[str, Any]:
        return service.state()

    @router.get("/pipelines", response_model=PipelinesResponse)
    def pipelines() -> dict[str, Any]:
        return {"pipelines": service.store.recent()}

    @router.get("/pipelines/{pipeline_id}")
    def pipeline_detail(pipeline_id: str) -> dict[str, Any]:
        for pipeline in service.store.recent(100):
            if pipeline.get("pipeline_id") == pipeline_id:
                return pipeline
        raise HTTPException(
            status_code=404,
            detail={"code": "pipeline_not_found", "message": "Pipeline not found"},
        )

    @router.post("/intents", response_model=IntentResponse)
    def intents(request: IntentRequest) -> dict[str, Any]:
        intent = request.intent.strip()
        if not intent:
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_intent", "message": "intent must be a non-empty string"},
            )
        context = service.run_intent(intent, request.execution_mode)
        payload = serialize_context(context)
        payload["execution_mode"] = request.execution_mode
        service.save_context(payload)
        return payload

    return router
