"""Explainable risk model for AI-driven state transitions.

Evaluates:
- Destructive operations
- Privilege escalation
- Production / protected resource impact
- External side effects
- Irreversibility
- Blast radius
- Intent uncertainty / ambiguities
- Verification conflicts
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ..domain.models import (
    Action,
    CandidateState,
    Conflict,
    Intent,
    RiskAssessment,
    RiskLevel,
    VerificationEvidence,
)


class RiskEngine:
    """Calculates explainable risk levels and factor decomposition."""

    DESTRUCTIVE_PATTERN = re.compile(
        r"\b(rm\s+-rf|drop\s+\w+|truncate|delete\s+from|delete\b|format\s+[a-z]:|wipe|destroy|uninstall)\b",
        re.IGNORECASE,
    )
    PRIVILEGE_PATTERN = re.compile(
        r"\b(sudo|chmod\s+777|setuid|grant\s+all|useradd|chown\s+root|passwd|privilege|admin)\b",
        re.IGNORECASE,
    )
    PROD_PATTERN = re.compile(
        r"(\bprod\b|production|mainnet|live_db|/etc/|/var/log|/secrets|/protected/|\.env)",
        re.IGNORECASE,
    )
    EGRESS_PATTERN = re.compile(
        r"\b(curl\s+|wget\s+|fetch|http://|https://|nc\s+-e|socket|ssh\s+)\b",
        re.IGNORECASE,
    )

    def __init__(self, high_risk_threshold: float = 40.0, critical_risk_threshold: float = 70.0):
        self.high_risk_threshold = high_risk_threshold
        self.critical_risk_threshold = critical_risk_threshold

    def evaluate(
        self,
        intent: Optional[Intent] = None,
        actions: Optional[List[Action]] = None,
        candidate_state: Optional[CandidateState] = None,
        verifications: Optional[List[VerificationEvidence]] = None,
        conflicts: Optional[List[Conflict]] = None,
    ) -> RiskAssessment:
        """Compute an explainable heuristic risk assessment from all available signals."""
        factors: List[str] = []
        details: Dict[str, Any] = {}
        score: float = 0.0

        # 1. Evaluate Intent Ambiguities and Disallowed Operations
        if intent:
            if intent.ambiguities:
                score += 15.0
                factors.append("intent_ambiguity")
                details["ambiguities"] = intent.ambiguities
            if intent.disallowed_operations:
                details["disallowed_operations"] = intent.disallowed_operations

            goal_text = intent.goal.lower()
            if self.DESTRUCTIVE_PATTERN.search(goal_text):
                score += 25.0
                factors.append("destructive_intent")
            if self.PRIVILEGE_PATTERN.search(goal_text):
                score += 30.0
                factors.append("privilege_escalation_intent")
            if self.PROD_PATTERN.search(goal_text):
                score += 25.0
                factors.append("production_resource_intent")

        # 2. Evaluate Proposed Actions
        if actions:
            total_actions = len(actions)
            details["action_count"] = total_actions
            has_destructive_action = False
            has_privilege_action = False
            has_egress_action = False

            for act in actions:
                payload_str = str(act.payload)
                target = act.target_path or ""
                combined_text = f"{act.action_type} {target} {payload_str}"

                if act.action_type in ("file_delete", "db_drop", "table_truncate") or self.DESTRUCTIVE_PATTERN.search(combined_text):
                    has_destructive_action = True
                if self.PRIVILEGE_PATTERN.search(combined_text):
                    has_privilege_action = True
                if act.action_type in ("http_request", "network_egress") or self.EGRESS_PATTERN.search(combined_text):
                    has_egress_action = True
                if self.PROD_PATTERN.search(target):
                    factors.append("touches_protected_path")
                    score += 20.0

            if has_destructive_action:
                score += 30.0
                factors.append("destructive_operation")
            if has_privilege_action:
                score += 35.0
                factors.append("privilege_escalation")
            if has_egress_action:
                score += 20.0
                factors.append("external_network_egress")

        # 3. Evaluate Candidate State / Blast Radius
        if candidate_state:
            modified_count = len(candidate_state.files_modified)
            added_count = len(candidate_state.files_added)
            deleted_count = len(candidate_state.files_deleted)
            total_affected = modified_count + added_count + deleted_count
            details["affected_resources_count"] = total_affected

            if deleted_count > 0:
                score += min(30.0, deleted_count * 10.0)
                factors.append("resource_deletion")
                details["deleted_resources"] = candidate_state.files_deleted

            if total_affected > 3:
                score += 15.0
                factors.append("broad_blast_radius")

            if candidate_state.side_effects:
                score += 15.0
                factors.append("external_side_effects")
                details["side_effects"] = candidate_state.side_effects

        # 4. Evaluate Verifications
        if verifications:
            fails = [v for v in verifications if v.status == "FAIL"]
            uncertains = [v for v in verifications if v.status == "UNCERTAIN"]
            details["verifier_fails"] = len(fails)
            details["verifier_uncertains"] = len(uncertains)

            if fails:
                # Any hard invariant failure escalates risk heavily
                penalty = sum(v.penalty if v.penalty > 0 else 20.0 for v in fails)
                score += min(50.0, penalty)
                factors.append("verification_failure")
            if uncertains:
                score += 20.0
                factors.append("verification_uncertainty")

        # 5. Evaluate Conflicts
        if conflicts:
            score += min(40.0, len(conflicts) * 20.0)
            factors.append("verifier_disagreement_conflict")
            details["conflict_count"] = len(conflicts)

        # Deduplicate factors
        factors = sorted(list(set(factors)))

        # Normalize score within 0.0 - 100.0
        normalized_score = min(100.0, max(0.0, round(score, 2)))

        # Determine Risk Level
        if normalized_score >= self.critical_risk_threshold:
            level = RiskLevel.CRITICAL
        elif normalized_score >= self.high_risk_threshold:
            level = RiskLevel.HIGH
        elif normalized_score >= 15.0:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        requires_auth = (
            level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
            or "destructive_intent" in factors
            or "destructive_operation" in factors
            or "resource_deletion" in factors
            or "privilege_escalation" in factors
            or "privilege_escalation_intent" in factors
            or "verifier_disagreement_conflict" in factors
        )

        return RiskAssessment(
            risk_level=level,
            score=normalized_score,
            factors=factors,
            requires_authorization=requires_auth,
            details=details,
        )
