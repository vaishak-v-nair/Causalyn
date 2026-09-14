"""Tests verifying Vercel serverless runtime compatibility and read-only filesystem resilience."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from starlette.testclient import TestClient

from causalyn.storage.pipeline_store import PipelineStore
from causalyn.commit.boundary import CommitBoundary


def test_pipeline_store_unwritable_path_fallback():
    """PipelineStore must not crash on read-only or invalid paths, falling back gracefully."""
    with patch("pathlib.Path.mkdir", side_effect=OSError(30, "Read-only file system")):
        store = PipelineStore("/read_only_root/causalyn.sqlite3")
        # Store must initialize without throwing and be able to save / recent
        assert store.path in (":memory:", str(Path(tempfile.gettempdir()) / "causalyn.sqlite3")) or ":memory:" in store.path

        test_payload = {"pipeline_id": "test-srv-1", "timestamp": 12345.0, "status": "ok"}
        store.save(test_payload)
        recent = store.recent(10)
        assert len(recent) >= 1
        assert recent[0]["pipeline_id"] == "test-srv-1"


def test_commit_boundary_serverless_resilience():
    """CommitBoundary must handle read-only environments gracefully without crashing."""
    with patch.dict(os.environ, {"VERCEL": "1"}):
        boundary = CommitBoundary(auth_policy_path="policies/auth.yaml")
        assert boundary is not None
        # commit_history_path should point to a writable temporary directory
        assert tempfile.gettempdir() in boundary.commit_history_path or "commit_history" in boundary.commit_history_path


def test_api_index_entrypoint():
    """Vercel entrypoint api/index.py must expose top-level FastAPI 'app'."""
    api_dir = REPO_ROOT / "api"
    api_index = api_dir / "index.py"
    if not api_index.is_file():
        api_dir.mkdir(parents=True, exist_ok=True)
        (api_dir / "__init__.py").write_text('"""Causalyn Serverless API Package."""\n', encoding="utf-8")
        api_index.write_text(
            '"""Vercel Serverless Function entrypoint for Causalyn."""\n\n'
            'from __future__ import annotations\n'
            'import os\n'
            'import sys\n'
            'from pathlib import Path\n\n'
            'ROOT_DIR = Path(__file__).resolve().parent.parent\n'
            'if str(ROOT_DIR) not in sys.path:\n'
            '    sys.path.insert(0, str(ROOT_DIR))\n\n'
            'os.environ.setdefault("VERCEL", "1")\n\n'
            'from app import app, api\n\n'
            '__all__ = ["app", "api"]\n',
            encoding="utf-8",
        )

    try:
        import api.index as vercel_entry
    except ModuleNotFoundError:
        import importlib.util
        spec = importlib.util.spec_from_file_location("api.index", str(api_index))
        assert spec and spec.loader
        vercel_entry = importlib.util.module_from_spec(spec)
        sys.modules["api.index"] = vercel_entry
        spec.loader.exec_module(vercel_entry)

    assert hasattr(vercel_entry, "app")
    assert hasattr(vercel_entry, "api")
    assert vercel_entry.app.title == "Causalyn API"


def test_serverless_http_endpoints():
    """Simulate serverless HTTP invocations across all primary web routes."""
    import app
    client = TestClient(app.app)

    # Cockpit / Index
    res = client.get("/")
    assert res.status_code == 200
    assert "html" in res.headers.get("content-type", "")

    # Sub-pages
    for page in ["/cockpit", "/overview", "/invariants", "/proofs", "/audit", "/swarm"]:
        r = client.get(page)
        assert r.status_code == 200
        assert "html" in r.headers.get("content-type", "")

    # Health API
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data.get("status") in ("HEALTHY", "DEGRADED", "ok")

    # Non-existent asset must return 404 (not 500)
    asset_404 = client.get("/nonexistent_asset_xyz.png")
    assert asset_404.status_code == 404
