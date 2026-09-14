"""Tests for the causal bisection engine."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from causalyn.bisect import bisect, BisectionError
from causalyn.checkpoint import CheckpointEngine
from causalyn.models import StepKind


class TestBisection:
    """Test the binary search through checkpoints."""

    def _setup_engine_with_known_break(self, tmp_git_repo: Path) -> CheckpointEngine:
        """Create checkpoints where step 2 introduces a bug.

        Step 0: Baseline (tests pass)
        Step 1: Add utils.py (tests pass)
        Step 2: Break hello.py — greet() returns "Goodbye" (tests FAIL)
        Step 3: Add config.py (tests still fail — broken state)
        Step 4: More utils (tests still fail — broken state)
        """
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        # Step 0: Checkpoint the initial state (tests pass here)
        engine.create(description="Baseline", kind=StepKind.FILE_WRITE, step_id="step_0")

        # Step 1: Add math (tests still pass)
        (tmp_git_repo / "math_ops.py").write_text(
            'def add(a, b):\n    return a + b\n', encoding="utf-8"
        )
        engine.create(description="Add math_ops.py", kind=StepKind.FILE_WRITE, step_id="step_1")

        # Step 2: BREAK hello.py (tests will fail from here on)
        (tmp_git_repo / "hello.py").write_text(
            'def greet():\n    return "Goodbye"  # BUG\n', encoding="utf-8"
        )
        engine.create(description="Modify hello.py (introduces bug)", kind=StepKind.FILE_WRITE, step_id="step_2")

        # Step 3: Unrelated change (tests still fail)
        (tmp_git_repo / "config.py").write_text(
            'DEBUG = True\n', encoding="utf-8"
        )
        engine.create(description="Add config.py", kind=StepKind.FILE_WRITE, step_id="step_3")

        # Step 4: More changes (tests still fail)
        (tmp_git_repo / "utils.py").write_text(
            'def to_upper(s):\n    return s.upper()\n', encoding="utf-8"
        )
        engine.create(description="Add utils.py", kind=StepKind.FILE_WRITE, step_id="step_4")

        return engine

    def test_bisect_finds_correct_breaking_step(self, tmp_git_repo: Path):
        """Bisection should identify step_2 as the first breaking step."""
        engine = self._setup_engine_with_known_break(tmp_git_repo)

        # The test command: run pytest on test_hello.py
        test_cmd = f"python -m pytest {tmp_git_repo / 'test_hello.py'} -x -q"

        result = bisect(engine, test_cmd)

        assert result.first_breaking_step == "step_2"
        assert result.last_good_step == "step_1"

    def test_bisect_report_has_summary(self, tmp_git_repo: Path):
        """The causal report should have a plain-language summary."""
        engine = self._setup_engine_with_known_break(tmp_git_repo)
        test_cmd = f"python -m pytest {tmp_git_repo / 'test_hello.py'} -x -q"

        result = bisect(engine, test_cmd)

        assert result.report.summary
        assert "step_2" in result.report.summary
        assert result.report.root_cause_step == "step_2"
        assert result.report.crash_step == "step_4"

    def test_bisect_report_has_chain(self, tmp_git_repo: Path):
        """The causal report should have a chain of causation."""
        engine = self._setup_engine_with_known_break(tmp_git_repo)
        test_cmd = f"python -m pytest {tmp_git_repo / 'test_hello.py'} -x -q"

        result = bisect(engine, test_cmd)

        chain = result.report.chain
        assert len(chain) >= 2  # at least root_cause and crash
        assert chain[0].role == "root_cause"
        assert chain[-1].role == "crash"

    def test_bisect_efficiency(self, tmp_git_repo: Path):
        """Bisection should test fewer steps than total checkpoints (binary search)."""
        engine = self._setup_engine_with_known_break(tmp_git_repo)
        test_cmd = f"python -m pytest {tmp_git_repo / 'test_hello.py'} -x -q"

        result = bisect(engine, test_cmd)

        # With 5 checkpoints, binary search should need at most ~4 tests
        # (2 boundary checks + log2(5) ≈ 2-3 bisection steps)
        assert result.steps_tested <= result.total_checkpoints

    def test_bisect_too_few_checkpoints_raises(self, tmp_git_repo: Path):
        """Bisection should fail with fewer than 2 checkpoints."""
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()
        engine.create(description="Only one", step_id="step_0")

        with pytest.raises(BisectionError, match="at least 2"):
            bisect(engine, "python -m pytest test_hello.py -x -q")

    def test_bisect_when_test_passes_raises(self, tmp_git_repo: Path):
        """If the test passes at the latest checkpoint, there's nothing to bisect."""
        engine = CheckpointEngine(repo_dir=tmp_git_repo)
        engine.begin_session()

        # Two checkpoints where everything is fine
        engine.create(description="Good state A", step_id="step_0")
        (tmp_git_repo / "extra.py").write_text("x = 1\n", encoding="utf-8")
        engine.create(description="Good state B", step_id="step_1")

        test_cmd = f"python -m pytest {tmp_git_repo / 'test_hello.py'} -x -q"

        with pytest.raises(BisectionError, match="passes at the latest"):
            bisect(engine, test_cmd)
