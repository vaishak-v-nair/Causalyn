"""Deterministic, local-first mission lifecycle orchestration.

The service deliberately delegates execution and safety decisions to
``AIOrchestrator``.  It adds a small typed lifecycle around that existing core;
it does not call providers or perform network I/O.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from ..commit.boundary import CommitStatus
from ..orchestrator.orchestrator import AIOrchestrator, OrchestrationContext
from ..verification.invariant_checker import Decision as VerificationDecision


class MissionState(Enum):
    """Ordered states of a mission lifecycle."""

    ANALYZE = "analyze"
    SHADOW = "shadow"
    VERIFY = "verify"
    AUTHORIZE = "authorize"
    COMMIT = "commit"


class Decision(Enum):
    """Terminal safety decision for a mission."""

    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"


MissionDecision = Decision


@dataclass(frozen=True)
class MissionAnalysis:
    """Provider-neutral facts derived from an intent string."""

    intent: str
    intent_fingerprint: str
    operation: str
    risk: str


@dataclass(frozen=True)
class MissionResult:
    """Immutable outcome and evidence for one local mission run."""

    mission_id: str
    state: MissionState
    decision: Decision
    analysis: MissionAnalysis
    states: Tuple[MissionState, ...]
    orchestration: Optional[OrchestrationContext] = None
    reason: Optional[str] = None


class MissionLifecycleService:
    """Run missions locally, with ``AIOrchestrator`` as the safety core."""

    _STATE_ORDER = (
        MissionState.ANALYZE,
        MissionState.SHADOW,
        MissionState.VERIFY,
        MissionState.AUTHORIZE,
        MissionState.COMMIT,
    )

    def __init__(self, orchestrator: AIOrchestrator):
        self.orchestrator = orchestrator

    def analyze(self, intent: str) -> MissionAnalysis:
        """Produce stable analysis without provider calls or side effects."""
        if not isinstance(intent, str) or not intent.strip():
            raise ValueError("intent must be a non-empty string")
        normalized = " ".join(intent.split())
        lowered = normalized.casefold()
        if re.search(r"\b(delete|remove|destroy|drop)\b", lowered):
            operation, risk = "delete", "high"
        elif re.search(r"\b(migrate|update|change|modify|fix|resolve)\b", lowered):
            operation, risk = "mutate", "medium"
        elif re.search(r"\b(build|create|add)\b", lowered):
            operation, risk = "create", "medium"
        else:
            operation, risk = "inspect", "low"
        fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return MissionAnalysis(normalized, fingerprint, operation, risk)

    def run(self, intent: str) -> MissionResult:
        """Execute one mission and return a fail-closed lifecycle result."""
        analysis = self.analyze(intent)
        mission_id = f"mission-{analysis.intent_fingerprint[:16]}"

        try:
            context = self.orchestrator.process_intent(analysis.intent)
        except Exception as exc:  # The service boundary must fail closed.
            return MissionResult(
                mission_id, MissionState.COMMIT, Decision.ESCALATE, analysis,
                self._STATE_ORDER, reason=f"orchestrator failure: {exc}",
            )

        verification = context.verification_decision
        record = context.commit_record
        if verification is VerificationDecision.DENY:
            decision, reason = Decision.DENY, "verification denied"
        elif verification is VerificationDecision.ESCALATE:
            decision, reason = Decision.ESCALATE, "verification requires review"
        elif verification is not VerificationDecision.ALLOW:
            decision, reason = Decision.ESCALATE, "missing verification decision"
        elif record is None:
            decision, reason = Decision.ESCALATE, "missing commit evidence"
        elif not record.authorization_given:
            decision, reason = Decision.DENY, "authorization denied"
        elif record.decision is CommitStatus.COMMITTED:
            decision, reason = Decision.ALLOW, None
        elif record.decision is CommitStatus.ESCALATED:
            decision, reason = Decision.ESCALATE, record.escalation_reason
        else:
            decision, reason = Decision.DENY, record.escalation_reason

        return MissionResult(
            mission_id=mission_id,
            state=MissionState.COMMIT,
            decision=decision,
            analysis=analysis,
            states=self._STATE_ORDER,
            orchestration=context,
            reason=reason,
        )

    execute = run
    run_mission = run
    execute_mission = run
