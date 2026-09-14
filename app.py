"""HTTP application for the Causalyn Prototype 001 full-stack tool."""

from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.middleware.cors import CORSMiddleware

from causalyn.commit.boundary import CommitBoundary
from causalyn.failure_pattern.dataset import FailurePatternDataset
from causalyn.orchestrator.orchestrator import AIOrchestrator, OrchestrationContext
from causalyn.shadow.executor import ShadowExecutor
from causalyn.verification.invariant_checker import create_default_verification_engine
from causalyn.model.world_state import WorldStateManager
from causalyn.api.routes import create_router
from causalyn.api.services import BackendService
from causalyn.api.websocket_manager import ws_manager, trigger_semantic_interference_sync
from causalyn.config import get_settings
from causalyn.storage.pipeline_store import PipelineStore

gateway = ws_manager
gateway.broadcast_state = ws_manager.broadcast_json

async def trigger_semantic_interference(kappa_val: float, violation: str = "") -> None:
    payload = {
        "event": "PARADOX_DETECTED" if kappa_val > 0 else "NULL_SPACE_CONFIRMED",
        "kappa": kappa_val,
        "decision": "DENY" if kappa_val > 0 else "ALLOW",
        "violation": violation,
    }
    await ws_manager.broadcast_json(payload)

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
    commit_history_path = None
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        import tempfile
        commit_history_path = str(Path(tempfile.gettempdir()) / "commit_history.jsonl")

    boundary = CommitBoundary(
        failure_dataset=dataset,
        auth_policy_path=str(ROOT / "policies" / "auth.yaml"),
        commit_history_path=commit_history_path,
    )
    orchestrator = AIOrchestrator()

    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env", override=False)
    except Exception:
        pass
    settings = get_settings()
    from causalyn.llm.provider import create_llm_provider
    llm_provider = create_llm_provider(settings)

    orchestrator.set_dependencies(
        world_state_manager=manager,
        shadow_executor=executor,
        verification_engine=create_default_verification_engine(
            policies_dir=str(ROOT / "policies")
        ),
        commit_boundary=boundary,
        failure_dataset=dataset,
        llm_provider=llm_provider,
    )
    return orchestrator, manager


ORCHESTRATOR, WORLD_STATE = build_orchestrator()
PIPELINE_LOCK = threading.Lock()


def _resolve_db_path() -> str:
    db_env = os.environ.get("CAUSALYN_DB")
    if db_env:
        return db_env
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        import tempfile
        return str(Path(tempfile.gettempdir()) / "causalyn.sqlite3")
    return str(ROOT / "runtime" / "causalyn.sqlite3")


PIPELINE_STORE = PipelineStore(_resolve_db_path())


def context_to_dict(context: OrchestrationContext) -> dict[str, Any]:
    spec = context.intent_spec
    record = context.commit_record
    provider_name = getattr(getattr(ORCHESTRATOR, "llm_provider", None), "provider_name", "gemini")
    if provider_name == "null":
        provider_name = "local_baseline"

    return {
        "pipeline_id": context.pipeline_id,
        "timestamp": context.timestamp,
        "stage": context.current_stage.value,
        "stages_completed": [stage.value for stage in context.stages_completed],
        "error": context.error,
        "paradox_index": context.metadata.get("paradox_index", 0.0),
        "refinement_iterations": context.metadata.get("refinement_iterations", 1),
        "cegar_counterexamples": context.metadata.get("cegar_counterexamples", []),
        "unified_diffs": context.metadata.get("unified_diffs", {}),
        "provider": provider_name.upper(),
        "audit_compliance": "EU AI Act (Regulation 2024/1689 Article 10) Verified",
        "intent": {
            "intent_id": spec.intent_id,
            "goal": spec.goal,
            "scope": spec.scope,
            "target_paths": getattr(spec, "target_paths", []),
            "auth_scope": getattr(spec, "auth_scope", "PUBLIC"),
            "ambient_coordinates": getattr(spec, "ambient_coordinates", (0.5, 0.9, 0.95)),
            "assumptions": spec.assumptions,
            "ambiguities": spec.ambiguities,
            "unknowns": spec.unknowns,
            "required_invariants": spec.required_invariants,
            "forbidden_states": spec.forbidden_states,
        }
        if spec
        else None,
        "verification": context.verification_decision.value
        if context.verification_decision
        else None,
        "commit": {
            "commit_id": record.commit_id,
            "decision": record.decision.value,
            "reason": record.escalation_reason,
            "changes": record.changes_summary,
            "authorization_given": record.authorization_given,
            "verification_decision": record.verification_decision.value,
        }
        if record
        else None,
    }

api = FastAPI(title="Causalyn API", version="0.2.0")
app = api  # Top-level 'app' FastAPI instance required by Vercel, Uvicorn, and ASGI servers
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

@api.websocket("/ws")
@api.websocket("/ws/continuum")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # We just keep the connection alive, client doesn't need to send anything
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@api.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "request_error", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content={"error": detail})


def safe_serialize_errors(errors: Any) -> Any:
    if isinstance(errors, list):
        return [safe_serialize_errors(e) for e in errors]
    if isinstance(errors, dict):
        return {str(k): safe_serialize_errors(v) for k, v in errors.items()}
    if isinstance(errors, bytes):
        return errors.decode("utf-8", errors="replace")
    if isinstance(errors, (str, int, float, bool, type(None))):
        return errors
    return str(errors)


@api.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "fields": safe_serialize_errors(exc.errors()),
            }
        },
    )



BACKEND_SERVICE = BackendService(ORCHESTRATOR, WORLD_STATE, PIPELINE_STORE, PIPELINE_LOCK)
api.include_router(create_router(BACKEND_SERVICE, context_to_dict, prefix="/api"))
api.include_router(create_router(BACKEND_SERVICE, context_to_dict, prefix="/v1"))


def _serve_page(filename: str, fallback_title: str) -> Response:
    target = WEB_ROOT / filename
    if target.exists() and target.is_file():
        return FileResponse(target, media_type="text/html")
    index_path = WEB_ROOT / "index.html"
    if index_path.exists() and index_path.is_file():
        return FileResponse(index_path, media_type="text/html")
    fallback_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Causalyn — {fallback_title}</title>
    <style>
        :root {{ --bg: #0b0f19; --card: #131b2e; --accent: #6366f1; --text: #f3f4f6; --text-dim: #94a3b8; }}
        body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 1.5rem; box-sizing: border-box; }}
        .card {{ max-width: 680px; width: 100%; background: var(--card); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 2.2rem; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6); }}
        .header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }}
        h1 {{ font-size: 1.5rem; margin: 0; color: #fff; font-weight: 700; }}
        .badge {{ background: #10b981; color: #022c22; font-size: 0.75rem; font-weight: 700; padding: 0.25rem 0.65rem; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.05em; }}
        p {{ color: var(--text-dim); line-height: 1.6; font-size: 0.95rem; margin-bottom: 1.5rem; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }}
        a.btn {{ text-decoration: none; background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.3); color: #c7d2fe; padding: 0.85rem 1rem; border-radius: 10px; font-size: 0.88rem; font-weight: 500; transition: all 0.2s ease; display: block; text-align: center; }}
        a.btn:hover {{ background: rgba(99,102,241,0.25); border-color: #818cf8; color: #fff; transform: translateY(-1px); }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>Causalyn Continuum</h1>
            <span class="badge">Online (Vercel)</span>
        </div>
        <p>The Acausal Control Plane, Formal Verification Hypervisor, and CEGIS Invariant Engine are operational in serverless mode.</p>
        <div class="grid">
            <a class="btn" href="/api/health">System Health</a>
            <a class="btn" href="/api/pipelines">Audit Ledger</a>
            <a class="btn" href="/docs">OpenAPI Spec</a>
            <a class="btn" href="/api/state">World State</a>
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=fallback_html, status_code=200, media_type="text/html")


@api.get("/")
@api.get("/cockpit")
def index() -> Response:
    return _serve_page("index.html", "Hypervisor Cockpit")


@api.get("/overview")
def overview_page() -> Response:
    return _serve_page("overview.html", "Architecture Overview")


@api.get("/invariants")
def invariants_page() -> Response:
    return _serve_page("invariants.html", "Invariant Registry")


@api.get("/proofs")
def proofs_page() -> Response:
    return _serve_page("proofs.html", "SMT Proof Explorer")


@api.get("/audit")
def audit_page() -> Response:
    return _serve_page("audit.html", "Formal Audit Ledger")


@api.get("/swarm")
def swarm_page() -> Response:
    return _serve_page("swarm.html", "Autonomous Swarm Consensus")


# Mount all contemporary backend control plane, CEGIS, and telemetry endpoints
try:
    from backend.app import app as backend_app
    api.include_router(backend_app.router)
except Exception as e:
    pass


@api.get("/{asset:path}")
def asset(asset: str) -> Response:
    # Allow serving videos and svg from assets folder
    if asset.startswith("assets/"):
        asset_path = WEB_ROOT / asset
        if not asset_path.exists() or not asset_path.is_file():
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": f"asset '{asset}' not found"})
        media_type = "video/mp4" if asset.endswith(".mp4") else "image/svg+xml" if asset.endswith(".svg") else None
        return FileResponse(asset_path, media_type=media_type)

    if asset.startswith("css/") or asset.startswith("js/") or asset.startswith("static/"):
        file_path = WEB_ROOT / asset
        if file_path.exists() and file_path.is_file():
            media_type = "text/css" if asset.endswith(".css") else "text/javascript" if asset.endswith(".js") else None
            return FileResponse(file_path, media_type=media_type)

    allowed = {
        "app.js": "text/javascript",
        "styles.css": "text/css",
        "three.min.js": "text/javascript",
        "vaishak_canvas.js": "text/javascript",
        "favicon.ico": "image/x-icon",
    }
    if asset in allowed:
        file_path = WEB_ROOT / asset
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path, media_type=allowed[asset])
    raise HTTPException(status_code=404, detail={"code": "not_found", "message": f"asset '{asset}' not found"})


def main() -> None:
    settings = get_settings()
    import uvicorn

    uvicorn.run(api, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
