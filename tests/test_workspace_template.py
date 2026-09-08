"""Unit and Integration Tests for Causalyn Acausal Workspace Templates."""

import pytest
import shutil
import tempfile
from pathlib import Path

from causalyn.workspace.template import (
    WorkspaceTemplateManager,
    AcausalWorkspaceConfig,
    DEFAULT_INVARIANTS_Z3,
)
from causalyn.workspace.runner import AcausalWorkspaceRunner, WorkspaceRunResult


@pytest.fixture
def temp_workspace():
    tmp_dir = Path(tempfile.mkdtemp(prefix="test_causalyn_ws_"))
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_init_workspace_scaffolding(temp_workspace):
    """Verify causalyn init generates all 3 template files with default invariants."""
    causalyn_dir = WorkspaceTemplateManager.init_workspace(
        target_dir=temp_workspace,
        project_name="test-project",
    )

    assert causalyn_dir.exists()
    assert (causalyn_dir / "invariants.z3").exists()
    assert (causalyn_dir / "seed_state.json").exists()
    assert (causalyn_dir / "manifest.toml").exists()

    # Re-init without force should raise FileExistsError
    with pytest.raises(FileExistsError):
        WorkspaceTemplateManager.init_workspace(target_dir=temp_workspace, force=False)

    # Re-init with force should succeed
    reinit_dir = WorkspaceTemplateManager.init_workspace(target_dir=temp_workspace, force=True)
    assert reinit_dir.exists()


def test_load_workspace(temp_workspace):
    """Verify loading and parsing of workspace configuration."""
    WorkspaceTemplateManager.init_workspace(temp_workspace, project_name="my-app")
    config = WorkspaceTemplateManager.load_workspace(temp_workspace)

    assert isinstance(config, AcausalWorkspaceConfig)
    assert config.project_name == "my-app"
    assert len(config.invariants_parsed) >= 3  # threads, memory, sockets
    assert "threads" in [inv["target_var"] for inv in config.invariants_parsed]
    assert config.permissions["allow_shell_exec"] is True


def test_workspace_runner_safe_mutation(temp_workspace):
    """Verify safe mutation commits atomically and produces 0 kappa."""
    WorkspaceTemplateManager.init_workspace(temp_workspace)
    runner = AcausalWorkspaceRunner(temp_workspace)

    target_file = "src/worker.py"
    content = "threads = 8\nmemory = 256\n"
    state_vars = {"threads": 8, "memory": 256}

    result = runner.run_mutation(
        target_file=target_file,
        proposed_content=content,
        state_variables=state_vars,
        agent_id="test-agent",
    )

    assert isinstance(result, WorkspaceRunResult)
    assert result.verdict == "COMMITTED"
    assert result.paradox_index == 0.0
    assert (temp_workspace / target_file).exists()
    assert (temp_workspace / target_file).read_text(encoding="utf-8") == content


def test_workspace_runner_cegis_autopatch(temp_workspace):
    """Verify hazardous concurrency bounds trigger CEGIS auto-patch and token savings."""
    WorkspaceTemplateManager.init_workspace(temp_workspace)
    runner = AcausalWorkspaceRunner(temp_workspace)

    target_file = "src/worker_heavy.py"
    content = "threads = 64\n"
    state_vars = {"threads": 64}

    result = runner.run_mutation(
        target_file=target_file,
        proposed_content=content,
        state_variables=state_vars,
        agent_id="claude-3-5-sonnet",
    )

    assert result.verdict == "COMMITTED"
    assert result.patch_applied is True
    assert result.tokens_conserved == 450
    assert result.avoided_crashes == 1
    # Check that auto-patched file exists on host disk
    assert (temp_workspace / target_file).exists()
    patched_code = (temp_workspace / target_file).read_text(encoding="utf-8")
    assert "threads = 16" in patched_code
