"""HTTP application for the Causalyn Prototype 001 full-stack tool."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from source.commit.boundary import CommitBoundary
from source.failure_pattern.dataset import FailurePatternDataset
from source.orchestrator.orchestrator import AIOrchestrator, OrchestrationContext
from source.shadow.executor import ShadowExecutor
from source.verification.invariant_checker import create_default_verification_engine
from source.model.world_state import WorldStateManager


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


def context_to_dict(context: OrchestrationContext) -> dict[str, Any]:
    spec = context.intent_spec
    record = context.commit_record
    return {
        "pipeline_id": context.pipeline_id,
        "stage": context.current_stage.value,
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
    server = ThreadingHTTPServer((host, port), CausalynHandler)
    print(f"Causalyn running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
