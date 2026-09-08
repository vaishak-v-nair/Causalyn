"""Unit Tests for Quantitative Telemetry and W&B Integration."""

import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from causalyn.telemetry.wandb_logger import (
    QuantitativeTelemetryTracker,
    WandbAcausalLogger,
    get_telemetry_tracker,
)
from backend.app import app


def test_quantitative_telemetry_tracker_accumulation():
    """Verify thread-safe metric accumulation and summary statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "metrics.jsonl"
        tracker = QuantitativeTelemetryTracker(offline_log_path=log_file)

        # Record clean run
        tracker.record_mutation(
            latency_us=42.5,
            tokens_conserved=0,
            avoided_crashes=0,
            kappa=0.0,
            verdict="COMMITTED",
        )

        # Record auto-patched run
        tracker.record_mutation(
            latency_us=65.0,
            tokens_conserved=450,
            avoided_crashes=1,
            kappa=1.0,
            verdict="COMMITTED",
        )

        summary = tracker.get_summary()
        assert summary["total_mutations_evaluated"] == 2
        assert summary["total_tokens_conserved"] == 450
        assert summary["total_avoided_crashes"] == 1
        assert summary["total_committed"] == 2
        assert summary["total_annihilated"] == 0
        assert summary["latest_latency_us"] == 65.0
        assert log_file.exists()


def test_idle_tracker_has_no_fake_latency():
    """Verify that an unexercised tracker reports true 0.0 metrics without fake baselines."""
    tracker = QuantitativeTelemetryTracker()
    summary = tracker.get_summary()
    assert summary["total_mutations_evaluated"] == 0
    assert summary["latest_latency_us"] == 0.0
    assert summary["mean_latency_us"] == 0.0
    assert summary["p50_latency_us"] == 0.0
    assert summary["p95_latency_us"] == 0.0
    assert summary["status"] == "idle"


def test_wandb_offline_fallback():
    """Verify WandbAcausalLogger writes structured offline metadata and history files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        offline_dir = Path(tmpdir) / "wandb_offline"
        logger = WandbAcausalLogger(project="test-project", enabled=False, offline_log_path=offline_dir)
        assert logger.is_online is False

        logger.init_run(run_name="test-run", config={"lr": 0.001})
        record = logger.log_mutation_result(
            latency_us=50.0,
            tokens_conserved=320,
            avoided_crashes=1,
            kappa=0.0,
            verdict="COMMITTED",
            agent_id="test-agent",
            target_file="test.py",
            commit_hash="0xabc123",
        )

        assert record["tokens_conserved"] == 320
        assert record["avoided_crashes"] == 1

        # Test artifact logging in offline mode
        dummy_cert = Path(tmpdir) / "audit.pdf"
        dummy_cert.write_bytes(b"%PDF-1.4 mock")
        logged = logger.log_certificate_artifact(dummy_cert, "a1b2c3d4e5f6")
        assert logged is True

        logger.finish()

        # Check offline directory contents
        assert (logger.offline_dir / "wandb-metadata.json").exists()
        assert (logger.offline_dir / "wandb-history.jsonl").exists()
        assert (logger.offline_dir / "wandb-summary.json").exists()
        assert (logger.offline_dir / "artifacts" / "cert-a1b2c3d4" / "audit.pdf").exists()


def test_telemetry_api_endpoint():
    """Verify GET /api/v1/telemetry/quantitative endpoint returns structured summary."""
    client = TestClient(app)
    resp = client.get("/api/v1/telemetry/quantitative")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_tokens_conserved" in data
    assert "total_avoided_crashes" in data
    assert "latest_latency_us" in data
