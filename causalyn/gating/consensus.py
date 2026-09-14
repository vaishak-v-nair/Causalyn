"""
Consensus gating layer – runs multiple verifiers per invariant and aggregates
results into ALLOW/DENY/ESCALATE decisions.
"""

from enum import Enum
from typing import List, Tuple, Callable, Optional
from ..model.world_state import WorldState


class Decision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"


class ConsensusGate:
    """
    Runs a list of verifier functions. Each verifier should return:
      True  -> invariant holds (vote for ALLOW)
      False -> invariant violated (vote for DENY)
      None  -> uncertain/unable to verify (vote for ESCALATE)
    Aggregation rules:
      - Any DENY -> DENY (fail‑closed)
      - Else, any ESCALATE -> ESCALATE (uncertainty)
      - Else, all ALLOW -> ALLOW
    """

    def __init__(self, verifiers: Optional[List[Tuple[Callable[[WorldState, WorldState], Optional[bool]], str]]] = None):
        """
        Args:
            verifiers: list of (verifier_func, description) tuples.
        """
        self.verifiers: List[Tuple[Callable[[WorldState, WorldState], Optional[bool]], str]] = verifiers or []

    def add_verifier(self, verifier: Callable[[WorldState, WorldState], Optional[bool]], description: str = ""):
        self.verifiers.append((verifier, description))

    def verify(self, before: WorldState, after: WorldState) -> Decision:
        has_deny = False
        has_escalate = False

        for verifier, desc in self.verifiers:
            try:
                result = verifier(before, after)
            except Exception as e:
                # Treat exceptions as uncertain
                result = None

            if result is False:
                has_deny = True
                # we could break early, but we continue to collect all info for logging
            elif result is None:
                has_escalate = True
            # result True -> ignore

        if has_deny:
            return Decision.DENY
        if has_escalate:
            return Decision.ESCALATE
        return Decision.ALLOW

    def get_verifier_details(self, before: WorldState, after: WorldState) -> List[dict]:
        """Return per-verifier outcome for audit/logging."""
        details = []
        for verifier, desc in self.verifiers:
            try:
                result = verifier(before, after)
            except Exception as e:
                result = None
                error = str(e)
            else:
                error = None
            details.append({
                "description": desc,
                "result": result,  # True/False/None
                "error": error
            })
        return details