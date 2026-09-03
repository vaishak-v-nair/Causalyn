"""HTTP application for the Causalyn Prototype 001 full-stack tool."""

from __future__ import annotations

import json
import os
import threading
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware

from source.commit.boundary import CommitBoundary
from source.failure_pattern.dataset import FailurePatternDataset
from source.orchestrator.orchestrator import AIOrchestrator, OrchestrationContext
from source.shadow.executor import ShadowExecutor
from source.verification.invariant_checker import create_default_verification_engine
from source.model.world_state import WorldStateManager
from source.api.contracts import IntentRequest
from source.storage.pipeline_store import PipelineStore


ROOT = Path(__file__).parent
WEB_ROOT = ROOT / "web"


def build_orchestrator() -> tuple[AIOrchestrator, WorldStateManager]:
    manager = WorldStateManager()
    manager.set_file_content(
        "/protected/config.json",
        {"debug": True, "secret_key": "redacted"},
    )
    manager.set_file_content(
        "/app/public/settings.json",
        {"feature_flag": False, "version": "1.0.0"},
    )
    dataset = FailurePatternDataset()
    executor = ShadowExecutor(manager)
    boundary = CommitBoundary(
        failure_dataset=dataset,
        auth_policy_path=str(ROOT / "policies" / "auth.yaml"),
    )
    orchestrator = AIOrchestrator()
    orchestrator.set_dependencies(
        world_state_manager=manager,
        shadow_executor=executor,
        verification_engine=create_default_verification_engine(
            policies_dir=str(ROOT / "policies")
        ),
        commit_boundary=boundary,
        failure_dataset=dataset,
    )
    return orchestrator, manager


ORCHESTRATOR, WORLD_STATE = build_orchestrator()
PIPELINE_LOCK = threading.Lock()


PIPELINE_STORE = PipelineStore(
    os.environ.get("CAUSALYN_DB", str(ROOT / "runtime" / "causalyn.sqlite3"))
)


def context_to_dict(context: OrchestrationContext) -> dict[str, Any]:
    spec = context.intent_spec
    record = context.commit_record
    return {
        "pipeline_id": context.pipeline_id,
        "timestamp": context.timestamp,
        "stage": context.current_stage.value,
        "stages_completed": [stage.value for stage in context.stages_completed],
        "error": context.error,
        "intent": {
            "intent_id": spec.intent_id,
            "goal": spec.goal,
            "ambiguities": spec.ambiguities,
            "forbidden_states": spec.forbidden_states,
        }
        if spec
        else None,
        "verification": context.verification_decision.value
        if context.verification_decision
        else None,
        "commit": {
            "decision": record.decision.value,
            "reason": record.escalation_reason,
            "changes": record.changes_summary,
        }
        if record
        else None,
    }

api = FastAPI(title="Causalyn API", version="0.2.0")
api.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
)


@api.middleware("http")
async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@api.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "request_error", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content={"error": detail})


@api.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "fields": exc.errors(),
                }
            },
        )


@api.get("/api/health")
def health() -> dict[str, str]:
        return {"status": "ok", "service": "causalyn", "maturity": "M1_TOY_PROTOTYPE"}


@api.get("/api/state")
def state() -> dict[str, Any]:
        with PIPELINE_LOCK:
            current = WORLD_STATE.get_current_state()
        return {
            "data": current.data,
            "files": sorted(current.file_system),
            "file_count": len(current.file_system),
        }


@api.get("/api/pipelines")
def pipelines() -> dict[str, Any]:
        return {"pipelines": PIPELINE_STORE.recent()}


@api.post("/api/intents")
def intents(request: IntentRequest) -> dict[str, Any]:
        intent = request.intent.strip()
        if not intent:
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_intent", "message": "intent must be a non-empty string"},
            )
        with PIPELINE_LOCK:
            context = ORCHESTRATOR.process_intent(intent)
            payload = context_to_dict(context)
            PIPELINE_STORE.save(payload)
        return payload


@api.get("/")
def index() -> FileResponse:
        return FileResponse(WEB_ROOT / "index.html")


@api.get("/{asset:path}")
def asset(asset: str) -> FileResponse:
        allowed = {"app.js": "text/javascript", "styles.css": "text/css"}
        if asset not in allowed:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "asset not found"})
        return FileResponse(WEB_ROOT / asset, media_type=allowed[asset])


class CausalynHandler(BaseHTTPRequestHandler):
    server_version = "Causalyn/0.1"

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/api/health":
            self._json(
                {
                    "status": "ok",
                    "service": "causalyn",
                    "maturity": "M1_TOY_PROTOTYPE",
                }
            )
        elif route == "/api/state":
            state = WORLD_STATE.get_current_state()
            self._json(
                {
                    "data": state.data,
                    "files": sorted(state.file_system),
                    "file_count": len(state.file_system),
                }
            )
        elif route == "/api/pipelines":
            self._json(
                {"pipelines": [context_to_dict(c) for c in ORCHESTRATOR.get_recent_pipelines()]}
            )
        elif route == "/" or route == "/index.html":
            self._file(WEB_ROOT / "index.html", "text/html; charset=utf-8")
        elif route in ("/app.js", "/styles.css"):
            content_type = "text/javascript; charset=utf-8" if route.endswith(".js") else "text/css; charset=utf-8"
            self._file(WEB_ROOT / route[1:], content_type)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/intents":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            intent = payload.get("intent")
            if not isinstance(intent, str) or not intent.strip():
                raise ValueError("intent must be a non-empty string")
            context = ORCHESTRATOR.process_intent(intent.strip())
            self._json(context_to_dict(context), HTTPStatus.OK)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def _json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, content_type: str) -> None:
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[causalyn] {format % args}")


def main() -> None:
    host = os.environ.get("CAUSALYN_HOST", "127.0.0.1")
    port = int(os.environ.get("CAUSALYN_PORT", "8000"))
    import uvicorn

    uvicorn.run(api, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
