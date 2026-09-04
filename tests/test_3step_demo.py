"""
Automated Verification Test Suite for the Causalyn 3-Step Prototype Demo.
Validates:
1. Step 1 (The Disaster): Un-gated execution modifies production and leaks secrets.
2. Step 2 (The Magic): Causalyn intercepts same prompt, executes in shadow sandbox,
   detects secret exfiltration, spikes kappa to 20.00, issues Consensus Gate DENY,
   and preserves production state completely unchanged.
3. Step 3 (The Explanation): API contract and CLI reproducibility.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import api
from demo import (
    DEMO_DIR,
    DEMO_PROMPT,
    DEMO_SECRET_TOKEN,
    read_production_settings,
    reset_demo_environment,
    run_step_1,
    run_step_2,
)


@pytest.fixture(autouse=True)
def clean_environment():
    """Ensure demo environment is pristine before and after each test."""
    reset_demo_environment()
    yield
    reset_demo_environment()


def test_step1_disaster_reproduced():
    """Step 1: Un-gated baseline execution modifies disk and exposes secret."""
    result = run_step_1()
    assert result["step"] == 1
    assert result["leaked"] is True
    assert result["production_state"] == "CORRUPTED"

    # Verify on physical disk
    disk_content = read_production_settings()
    assert "api_secret_key" in disk_content
    assert disk_content["api_secret_key"] == DEMO_SECRET_TOKEN


def test_step2_reset_environment():
    """Verify that reset_demo_environment cleanly restores pristine state."""
    # First corrupt it
    run_step_1()
    corrupted_content = read_production_settings()
    assert "api_secret_key" in corrupted_content

    # Now reset
    reset_demo_environment()
    clean_content = read_production_settings()
    assert "api_secret_key" not in clean_content
    assert clean_content.get("app_name") == "CausalynDemoApp"
    assert clean_content.get("version") == "1.0.0"


def test_step2_magic_causalyn_interception():
    """Step 2: Same prompt through Causalyn is intercepted, verified, denied, and production unchanged."""
    res_summary, mission = run_step_2()

    assert res_summary["step"] == 2
    assert res_summary["prompt"] == DEMO_PROMPT
    assert res_summary["decision"] == "DENY"
    assert res_summary["kappa"] >= 20.0
    assert "Credential leak detected in shadow state" in res_summary["reason"]

    # Verify physical disk state was NOT modified
    disk_content = read_production_settings()
    assert "api_secret_key" not in disk_content
    assert DEMO_SECRET_TOKEN not in json.dumps(disk_content)
    assert res_summary["production_state"] == "UNCHANGED"

    # Verify verifier matrix
    verifications = mission.verifications
    secret_fails = [v for v in verifications if "secret" in v.verifier and v.status == "FAIL"]
    assert len(secret_fails) >= 2, "Expected primary and secondary secret verifiers to fail"


def test_api_demo_mission_flow():
    """Verify that web API /api/missions correctly processes the demo prompt."""
    client = TestClient(api)
    resp = client.post(
        "/api/missions",
        json={"intent": DEMO_PROMPT, "auto_run": True},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["state"] == "denied"
    assert data["decision"]["outcome"] == "deny"
    assert data["decision"]["paradox_index"] >= 20.0
    assert "Credential leak detected in shadow state" in data["decision"]["reason"]

    # Check that candidate state captured the exfiltrated diff
    diffs = data["candidate_state"]["unified_diffs"]
    assert "/app/public/settings.json" in diffs
    assert DEMO_SECRET_TOKEN in diffs["/app/public/settings.json"]


def test_demo_py_cli_execution():
    """Verify that python demo.py runs end-to-end via CLI with exit code 0."""
    res = subprocess.run(
        [sys.executable, "demo.py"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    assert res.returncode == 0, f"demo.py failed with error: {res.stderr}"
    assert "STARTING CAUSALYN 3-STEP PROTOTYPE DEMONSTRATION" in res.stdout
    assert "STEP 1 -- THE DISASTER: UN-GATED BASELINE EXECUTION" in res.stdout
    assert "STEP 2 -- THE MAGIC: CAUSALYN INTERCEPTED SHADOW EXECUTION" in res.stdout
    assert "STEP 3 -- THE EXPLANATION: TELEMETRY, EVIDENCE & PROOF" in res.stdout
    assert "ACTION REJECTED Production State: UNCHANGED" in res.stdout
