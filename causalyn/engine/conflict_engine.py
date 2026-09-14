"""Conflict Analysis Engine for verifier and model disagreements.

Treats disagreement as a first-class product event rather than averaging it away.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from ..domain.models import Conflict, VerificationEvidence


class ConflictEngine:
    """Analyzes verification evidence to detect and isolate conflicts."""

    def detect_conflicts(
        self, evidences: List[VerificationEvidence]
    ) -> List[Conflict]:
        """Detect pairwise disagreements across verifiers for each invariant/target."""
        conflicts: List[Conflict] = []
        # Group evidence by invariant or category
        grouped: Dict[str, List[VerificationEvidence]] = {}

        for ev in evidences:
            inv_key = ev.details.get("invariant_id") or ev.verifier.split(":")[0]
            grouped.setdefault(inv_key, []).append(ev)

        for inv_id, ev_list in grouped.items():
            if len(ev_list) < 2:
                continue

            # Check for conflicting verdicts
            passes = [e for e in ev_list if e.status == "PASS"]
            fails = [e for e in ev_list if e.status == "FAIL"]
            uncertains = [e for e in ev_list if e.status == "UNCERTAIN"]

            # Conflict Case 1: Direct Contradiction (PASS vs FAIL)
            if passes and fails:
                for p in passes:
                    for f in fails:
                        c_id = f"conf-{uuid.uuid4().hex[:8]}"
                        conflicts.append(
                            Conflict(
                                conflict_id=c_id,
                                invariant_id=inv_id,
                                verifier_a=p.verifier,
                                verifier_b=f.verifier,
                                verdict_a=p.status,
                                verdict_b=f.status,
                                description=(
                                    f"Direct conflict on invariant '{inv_id}': "
                                    f"{p.verifier} passed, but {f.verifier} reported violation ({f.message})"
                                ),
                                affected_invariant=inv_id,
                                resolution_strategy="escalate_to_human",
                                timestamp=time.time(),
                            )
                        )

            # Conflict Case 2: Divergence with Uncertainty (PASS vs UNCERTAIN)
            elif passes and uncertains:
                for p in passes:
                    for u in uncertains:
                        c_id = f"conf-{uuid.uuid4().hex[:8]}"
                        conflicts.append(
                            Conflict(
                                conflict_id=c_id,
                                invariant_id=inv_id,
                                verifier_a=p.verifier,
                                verifier_b=u.verifier,
                                verdict_a=p.status,
                                verdict_b=u.status,
                                description=(
                                    f"Unresolved divergence on invariant '{inv_id}': "
                                    f"{p.verifier} passed, while {u.verifier} reported uncertainty ({u.message})"
                                ),
                                affected_invariant=inv_id,
                                resolution_strategy="escalate_to_human",
                                timestamp=time.time(),
                            )
                        )

        return conflicts

    def summarize_conflicts(self, conflicts: List[Conflict]) -> Dict[str, Any]:
        """Produce an executive summary of conflicts for UI and audit."""
        if not conflicts:
            return {"count": 0, "conflicts": [], "requires_escalation": False}

        affected_invariants = list({c.affected_invariant for c in conflicts})
        return {
            "count": len(conflicts),
            "requires_escalation": True,
            "affected_invariants": affected_invariants,
            "conflicts": [c.to_dict() for c in conflicts],
        }
