"""Pydantic models for checkpoints, causal reports, and verification verdicts."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StepKind(str, Enum):
    """What the agent did at this step."""
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    COMMAND_RUN = "command_run"
    TEST_RUN = "test_run"
    UNKNOWN = "unknown"


class Checkpoint(BaseModel):
    """A single snapshot of the working tree at one agent step."""

    step_id: str = Field(description="Unique identifier for this step (e.g. 'step_004')")
    step_index: int = Field(description="Ordinal position in the run (0-based)")
    git_sha: str = Field(description="SHA of the git commit that captured this state")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = Field(default="", description="Human-readable description of what this step did")
    kind: StepKind = Field(default=StepKind.UNKNOWN)
    files_changed: list[str] = Field(default_factory=list, description="Paths modified in this step")


class CausalLink(BaseModel):
    """One link in the chain of causation from root cause to crash."""

    step_id: str
    step_index: int
    description: str
    role: str = Field(description="'root_cause', 'propagation', or 'crash'")


class CausalReport(BaseModel):
    """The plain-language report identifying why a run failed."""

    root_cause_step: str = Field(description="Step ID of the first step that introduced the fault")
    crash_step: str = Field(description="Step ID where the failure surfaced")
    chain: list[CausalLink] = Field(
        default_factory=list,
        description="Ordered list from root cause through propagation steps to crash"
    )
    summary: str = Field(description="Plain-language summary suitable for a terminal printout")
    diff_at_root_cause: str = Field(default="", description="git diff output at the root-cause step")
    test_command: str = Field(default="", description="The test command that was used to detect the failure")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VerificationVerdict(BaseModel):
    """Result of cross-vendor independent verification of a proposed fix."""

    agrees: bool = Field(description="Does the independent model agree the fix addresses the root cause?")
    concerns: list[str] = Field(
        default_factory=list,
        description="Specific concerns raised by the independent model"
    )
    recommendation: str = Field(default="", description="What the independent model recommends instead")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Model's self-reported confidence (0.0–1.0)"
    )
    model_used: str = Field(default="", description="Which model provided this verdict (e.g. 'openai/gpt-4o')")
    raw_response: str = Field(default="", description="Full text response from the verification model")
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BisectionResult(BaseModel):
    """Output of the causal bisection search."""

    first_breaking_step: str = Field(description="Step ID where the test first started failing")
    last_good_step: str = Field(description="Step ID of the last step where the test still passed")
    total_checkpoints: int = Field(description="How many checkpoints existed")
    steps_tested: int = Field(description="How many checkpoints were actually tested during bisection")
    report: CausalReport = Field(description="The full causal report")
