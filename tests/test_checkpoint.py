"""Tests for the git-based checkpoint engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from causalyn.checkpoint import CheckpointEngine, CheckpointError
from causalyn.models import StepKind


class TestCheckpointCreate:
    """Test creating checkpoints."""

    def test_create_checkpoint_returns_checkpoint(self, tmp_git_repo: Path):
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        cp = engine.create(description="First step", kind=StepKind.FILE_WRITE)

        assert cp.step_id == "step_0000"
        assert cp.step_index == 0
        assert cp.git_sha  # non-empty SHA
        assert cp.description == "First step"
        assert cp.kind == StepKind.FILE_WRITE

    def test_create_multiple_checkpoints_increments(self, tmp_git_repo: Path):
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        cp0 = engine.create(description="Step zero")
        cp1 = engine.create(description="Step one")
        cp2 = engine.create(description="Step two")

        assert cp0.step_index == 0
        assert cp1.step_index == 1
        assert cp2.step_index == 2
        assert cp0.git_sha != cp1.git_sha  # different commits (unless tree is identical)

    def test_create_with_custom_step_id(self, tmp_git_repo: Path):
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        cp = engine.create(description="Custom", step_id="my_step")

        assert cp.step_id == "my_step"

    def test_create_captures_file_changes(self, tmp_git_repo: Path):
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        # Create initial checkpoint
        engine.create(description="Baseline")

        # Modify a file
        (tmp_git_repo / "new_file.py").write_text("x = 1\n", encoding="utf-8")

        cp = engine.create(description="Added new_file.py")
        assert "new_file.py" in cp.files_changed


class TestCheckpointList:
    """Test listing checkpoints."""

    def test_list_all_empty(self, tmp_git_repo: Path):
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        assert engine.list_all() == []

    def test_list_all_returns_checkpoints(self, tmp_git_repo: Path):
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        engine.create(description="A")
        engine.create(description="B")

        checkpoints = engine.list_all()
        assert len(checkpoints) == 2
        assert checkpoints[0].description == "A"
        assert checkpoints[1].description == "B"


class TestCheckpointGet:
    """Test looking up checkpoints by step_id."""

    def test_get_existing(self, tmp_git_repo: Path):
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        engine.create(description="Target", step_id="target_step")

        cp = engine.get("target_step")
        assert cp.description == "Target"

    def test_get_nonexistent_raises(self, tmp_git_repo: Path):
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        with pytest.raises(CheckpointError, match="No checkpoint found"):
            engine.get("nonexistent")


class TestCheckpointRestore:
    """Test restoring to a checkpoint."""

    def test_restore_reverts_file_content(self, tmp_git_repo: Path):
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        # Checkpoint with original content
        engine.create(description="Original state", step_id="original")

        # Modify the file
        hello = tmp_git_repo / "hello.py"
        hello.write_text('def greet():\n    return "Modified"\n', encoding="utf-8")
        engine.create(description="Modified state", step_id="modified")

        # Restore to original
        engine.restore("original")

        content = hello.read_text(encoding="utf-8")
        assert '"Hello"' in content
        assert '"Modified"' not in content


class TestCheckpointDiff:
    """Test diffing between checkpoints."""

    def test_diff_shows_changes(self, tmp_git_repo: Path):
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        engine.create(description="Before", step_id="before")

        # Modify file
        (tmp_git_repo / "hello.py").write_text(
            'def greet():\n    return "Changed"\n', encoding="utf-8"
        )
        engine.create(description="After", step_id="after")

        diff = engine.diff("before", "after")
        assert "Hello" in diff or "Changed" in diff  # diff shows the change
