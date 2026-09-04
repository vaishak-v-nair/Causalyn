"""Application service adapters for HTTP routes.

The adapter intentionally delegates mission execution to the existing
orchestrator.  It owns no lifecycle or safety policy.
"""

from __future__ import annotations

import json
import threading
from typing import Any, Protocol

from causalyn.model.world_state import WorldStateManager
from causalyn.storage.pipeline_store import PipelineStore


class _Orchestrator(Protocol):
    def process_intent(self, intent: str, execution_mode: str = "shadow") -> Any: ...


class BackendService:
    """Serialize access to an already-configured orchestration core."""

    def __init__(
        self,
        orchestrator: _Orchestrator,
        world_state: WorldStateManager,
        store: PipelineStore,
        lock: threading.Lock | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.world_state = world_state
        self.store = store
        self.lock = lock or threading.Lock()

    def run_intent(self, intent: str, execution_mode: str = "shadow") -> Any:
        with self.lock:
            return self.orchestrator.process_intent(intent, execution_mode)

    def state(self) -> dict[str, Any]:
        with self.lock:
            current = self.world_state.get_current_state()
        return {
            "data": current.data,
            "files": sorted(current.file_system),
            "file_count": len(current.file_system),
        }

    def get_file_details(self) -> list[dict[str, Any]]:
        with self.lock:
            current = self.world_state.get_current_state()
            files_out = []
            protected_prefixes = ("/protected/", "/secrets/", "/config/", "/.env")
            for path, content in sorted(current.file_system.items()):
                raw_str = content if isinstance(content, str) else json.dumps(content, indent=2)
                files_out.append({
                    "path": path,
                    "is_protected": any(path.startswith(p) for p in protected_prefixes),
                    "size": len(raw_str),
                    "lines": len(raw_str.splitlines()),
                    "type": "json" if path.endswith(".json") else "python" if path.endswith(".py") else "text",
                })
            return files_out

    def get_file_content(self, path: str) -> str | None:
        with self.lock:
            current = self.world_state.get_current_state()
            content = current.file_system.get(path)
            if content is None:
                return None
            return content if isinstance(content, str) else json.dumps(content, indent=2)

    def save_context(self, payload: dict[str, Any]) -> None:
        self.store.save(payload)
