"""Causal bisection engine.

Binary-searches through checkpoints to find the first step that caused
a downstream test failure.  Produces a CausalReport with a plain-language
explanation of the causal chain.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .checkpoint import CheckpointEngine
from .models import (
    BisectionResult,
    CausalLink,
    CausalReport,
    Checkpoint,
)


class BisectionError(Exception):
    """Raised when bisection cannot proceed."""


def _run_test(test_command: str, cwd: Path, timeout: int = 60) -> bool:
    try:
        result = subprocess.run(
            test_command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def bisect(
    engine: CheckpointEngine,
    test_command: str,
    timeout_per_test: int = 60,
) -> BisectionResult:
    """Binary-search through checkpoints to find the first breaking step.

    Preconditions:
    - At least 2 checkpoints exist.
    - The test currently fails (i.e. the latest checkpoint is broken).
    - The test passed at some earlier checkpoint (ideally the first one).

    The algorithm restores each candidate checkpoint, runs the test, and
    narrows down to the first step where the test transitions from
    pass → fail.
    """
    checkpoints = engine.list_all()
    if len(checkpoints) < 2:
        raise BisectionError(
            f"Need at least 2 checkpoints to bisect, found {len(checkpoints)}"
        )

    steps_tested = 0

    # Verify the last checkpoint is indeed broken
    engine.restore(checkpoints[-1].step_id)
    last_passes = _run_test(test_command, engine.repo_dir, timeout_per_test)
    steps_tested += 1
    if last_passes:
        raise BisectionError(
            "The test passes at the latest checkpoint — nothing to bisect."
        )

    # Verify the first checkpoint is good
    engine.restore(checkpoints[0].step_id)
    first_passes = _run_test(test_command, engine.repo_dir, timeout_per_test)
    steps_tested += 1
    if not first_passes:
        # Edge case: the very first step was already broken.
        # The root cause IS step 0.
        report = _build_report(
            engine=engine,
            root_cause=checkpoints[0],
            crash=checkpoints[-1],
            checkpoints=checkpoints,
            test_command=test_command,
        )
        return BisectionResult(
            first_breaking_step=checkpoints[0].step_id,
            last_good_step=checkpoints[0].step_id,  # no known good state
            total_checkpoints=len(checkpoints),
            steps_tested=steps_tested,
            report=report,
        )

    # Binary search: lo is the last known-good, hi is the first known-bad
    lo = 0
    hi = len(checkpoints) - 1

    while hi - lo > 1:
        mid = (lo + hi) // 2
        engine.restore(checkpoints[mid].step_id)
        passes = _run_test(test_command, engine.repo_dir, timeout_per_test)
        steps_tested += 1

        if passes:
            lo = mid
        else:
            hi = mid

    # checkpoints[lo] is the last good, checkpoints[hi] is the first bad
    last_good = checkpoints[lo]
    first_bad = checkpoints[hi]

    # Restore the original working tree so the agent isn't left in a
    # weird state after bisection
    engine.restore_original()

    report = _build_report(
        engine=engine,
        root_cause=first_bad,
        crash=checkpoints[-1],
        checkpoints=checkpoints,
        test_command=test_command,
    )

    return BisectionResult(
        first_breaking_step=first_bad.step_id,
        last_good_step=last_good.step_id,
        total_checkpoints=len(checkpoints),
        steps_tested=steps_tested,
        report=report,
    )


def _build_report(
    *,
    engine: CheckpointEngine,
    root_cause: Checkpoint,
    crash: Checkpoint,
    checkpoints: list[Checkpoint],
    test_command: str,
) -> CausalReport:
    """Construct a CausalReport from bisection results."""
    chain: list[CausalLink] = []

    # Root cause link
    chain.append(CausalLink(
        step_id=root_cause.step_id,
        step_index=root_cause.step_index,
        description=root_cause.description or f"Changes at {root_cause.step_id}",
        role="root_cause",
    ))

    # Propagation links: steps between root cause and crash
    for cp in checkpoints:
        if cp.step_index > root_cause.step_index and cp.step_index < crash.step_index:
            chain.append(CausalLink(
                step_id=cp.step_id,
                step_index=cp.step_index,
                description=cp.description or f"Built on broken state at {cp.step_id}",
                role="propagation",
            ))

    # Crash link
    if crash.step_id != root_cause.step_id:
        chain.append(CausalLink(
            step_id=crash.step_id,
            step_index=crash.step_index,
            description=crash.description or f"Failure surfaced at {crash.step_id}",
            role="crash",
        ))

    # Get the diff at the root cause step
    diff_text = ""
    if root_cause.step_index > 0:
        prev_step = checkpoints[root_cause.step_index - 1]
        try:
            diff_text = engine.diff(prev_step.step_id, root_cause.step_id)
        except Exception:
            diff_text = "(diff unavailable)"

    # Build plain-language summary
    propagation_count = crash.step_index - root_cause.step_index - 1
    if propagation_count > 0:
        propagation_note = (
            f"Steps {root_cause.step_index + 1}–{crash.step_index - 1} "
            f"built on the broken state without detecting it."
        )
    else:
        propagation_note = "The failure surfaced immediately after the breaking change."

    summary = (
        f"Root cause: {root_cause.step_id} "
        f"({root_cause.description or 'unknown change'}). "
        f"{propagation_note} "
        f"Crash at {crash.step_id} "
        f"({crash.description or 'test failure'})."
    )

    return CausalReport(
        root_cause_step=root_cause.step_id,
        crash_step=crash.step_id,
        chain=chain,
        summary=summary,
        diff_at_root_cause=diff_text,
        test_command=test_command,
    )
