"""Domain entities and contracts for Causalyn execution control plane.

Encapsulates the core lifecycle:
Human Intent -> Intent Understanding -> Relevant State -> Proposed Action ->
Shadow Execution -> Verification -> Conflict Analysis -> Decision ->
Authorization -> Commit -> Audit.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class MissionState(str, Enum):
    """Explicit lifecycle stages of a Causalyn mission."""
    PENDING = "pending"
    ANALYZE = "analyze"
    SHADOW = "shadow"
    VERIFY = "verify"
    AUTHORIZE = "authorize"
    COMMIT = "commit"
    COMMITTED = "committed"
    DENIED = "denied"
    REJECTED = "rejected"
    FAILED = "failed"


class DecisionOutcome(str, Enum):
    """Terminal decision for a proposed state transition."""
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"


class RiskLevel(str, Enum):
    """Explainable risk levels for proposed mutations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VerifierLayer(str, Enum):
    """Tier of verification."""
    DETERMINISTIC = "deterministic"
    POLICY = "policy"
    STRUCTURAL = "structural"
    TEST = "test"
    ADVERSARIAL = "adversarial"
    MULTI_MODEL = "multi_model"


class AuthorizationStatus(str, Enum):
    """Status of human authorization gate."""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Intent:
    """Structured representation of human intent."""
    intent_id: str
    goal: str
    scope: Dict[str, List[str]] = field(default_factory=lambda: {"included": [], "excluded": []})
    target_paths: List[str] = field(default_factory=list)
    auth_scope: str = "PUBLIC"
    constraints: List[str] = field(default_factory=list)
    required_invariants: List[str] = field(default_factory=list)
    forbidden_states: List[str] = field(default_factory=list)
    allowed_operations: List[str] = field(default_factory=list)
    disallowed_operations: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    ambiguities: List[str] = field(default_factory=list)
    acceptance_conditions: List[str] = field(default_factory=list)
    ambient_coordinates: Tuple[float, float, float] = (0.5, 0.9, 0.95)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StateSnapshot:
    """Explicit representation of relevant system state."""
    state_id: str
    parent_state_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    environment: str = "local"
    resources: List[str] = field(default_factory=list)
    file_system: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    policies: List[str] = field(default_factory=list)
    provenance_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Action:
    """Concrete proposed action."""
    action_id: str
    action_type: str
    target_path: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateState:
    """State resulting from executing proposed actions in shadow sandbox."""
    candidate_id: str
    parent_state_id: str
    unified_diffs: Dict[str, str] = field(default_factory=dict)
    files_modified: Dict[str, Any] = field(default_factory=dict)
    files_added: Dict[str, Any] = field(default_factory=dict)
    files_deleted: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationEvidence:
    """Structured evidence produced by a single verifier."""
    verifier: str
    layer: VerifierLayer
    status: str  # "PASS", "FAIL", "UNCERTAIN"
    penalty: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["layer"] = self.layer.value if isinstance(self.layer, VerifierLayer) else str(self.layer)
        return d


VerificationResult = VerificationEvidence


@dataclass
class Conflict:
    """First-class product event representing verifier disagreement."""
    conflict_id: str
    invariant_id: str
    verifier_a: str
    verifier_b: str
    verdict_a: str
    verdict_b: str
    description: str
    affected_invariant: str
    resolution_strategy: str = "escalate_to_human"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskAssessment:
    """Explainable risk assessment model."""
    risk_level: RiskLevel
    score: float  # Heuristic score 0.0 - 100.0
    factors: List[str] = field(default_factory=list)
    requires_authorization: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["risk_level"] = self.risk_level.value if isinstance(self.risk_level, RiskLevel) else str(self.risk_level)
        return d


@dataclass
class Decision:
    """Terminal decision evaluating verification, conflicts, and risk."""
    outcome: DecisionOutcome
    reason: str
    paradox_index: float = 0.0
    counterexamples: List[Dict[str, Any]] = field(default_factory=list)
    escalation_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["outcome"] = self.outcome.value if isinstance(self.outcome, DecisionOutcome) else str(self.outcome)
        return d


@dataclass
class AuthorizationRequest:
    """Authorization view and record for high-impact or escalated actions."""
    auth_id: str
    mission_id: str
    affected_resources: List[str] = field(default_factory=list)
    changes_summary: Dict[str, Any] = field(default_factory=dict)
    risk_summary: Dict[str, Any] = field(default_factory=dict)
    verification_summary: Dict[str, Any] = field(default_factory=dict)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    rollback_available: bool = True
    status: AuthorizationStatus = AuthorizationStatus.NOT_REQUIRED
    approved_by: Optional[str] = None
    authorized_at: Optional[float] = None
    comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, AuthorizationStatus) else str(self.status)
        return d


@dataclass
class CommitRecord:
    """Audit record of commit boundary transition."""
    commit_id: str
    mission_id: str
    pre_state_hash: str
    post_state_hash: Optional[str]
    authorization_id: Optional[str]
    decision: str
    changes_summary: Dict[str, Any] = field(default_factory=dict)
    committed_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditRecord:
    """Immutable audit record reconstructible under EU AI Act Article 10."""
    audit_id: str
    mission_id: str
    timestamp: float = field(default_factory=time.time)
    lifecycle_events: List[Dict[str, Any]] = field(default_factory=list)
    evidence_chain: List[Dict[str, Any]] = field(default_factory=list)
    hash_signature: str = ""
    article_10_compliant: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Mission:
    """The root aggregate representing a consequential AI task."""
    mission_id: str
    state: MissionState = MissionState.PENDING
    intent: Optional[Intent] = None
    state_before: Optional[StateSnapshot] = None
    actions: List[Action] = field(default_factory=list)
    candidate_state: Optional[CandidateState] = None
    verifications: List[VerificationEvidence] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)
    risk: Optional[RiskAssessment] = None
    decision: Optional[Decision] = None
    authorization: Optional[AuthorizationRequest] = None
    commit: Optional[CommitRecord] = None
    audit_record: Optional[AuditRecord] = None
    latency_ms: Dict[str, float] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "state": self.state.value if isinstance(self.state, MissionState) else str(self.state),
            "intent": self.intent.to_dict() if self.intent else None,
            "state_before": {
                "state_id": self.state_before.state_id,
                "timestamp": self.state_before.timestamp,
                "resources": self.state_before.resources,
                "provenance_hash": self.state_before.provenance_hash,
            } if self.state_before else None,
            "actions": [a.to_dict() for a in self.actions],
            "candidate_state": self.candidate_state.to_dict() if self.candidate_state else None,
            "verifications": [v.to_dict() for v in self.verifications],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "risk": self.risk.to_dict() if self.risk else None,
            "decision": self.decision.to_dict() if self.decision else None,
            "authorization": self.authorization.to_dict() if self.authorization else None,
            "commit": self.commit.to_dict() if self.commit else None,
            "audit_record": self.audit_record.to_dict() if self.audit_record else None,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
