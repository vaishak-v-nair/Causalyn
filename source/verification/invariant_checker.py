"""
Verification Engine - evaluates invariants on shadow state and produces ALLOW/DENY/ESCALATE decisions.
Uses ConsensusGate for multi-verifier agreement.
Loads policies from YAML files.
"""

import yaml
import os
from enum import Enum
from typing import List, Dict, Any, Callable, Optional, Tuple
from ..model.world_state import WorldState
from ..gating.consensus import ConsensusGate, Decision


class InvariantViolation(Exception):
    """Raised when an invariant is violated."""
    def __init__(self, invariant: str, description: str):
        self.invariant = invariant
        self.description = description
        super().__init__(f"Invariant violation: {invariant} - {description}")


class VerificationEngine:
    """Evaluates invariants and makes verification decisions using consensus gating."""

    def __init__(self, policies_dir: str = "policies"):
        # each invariant: dict with id, description, verifiers(list of (callable,desc)), severity
        self.invariants: List[Dict[str, Any]] = []
        self.policy = {
            'fail_on_violation': True,  # DENY on any invariant violation
            'escalate_on_uncertainty': True,  # ESCALATE if we can't verify
        }
        self._load_policies(policies_dir)

    def _load_policies(self, policies_dir: str):
        """Load protection policies from YAML files."""
        invariants_path = os.path.join(policies_dir, "invariants.yaml")
        if os.path.exists(invariants_path):
            with open(invariants_path, 'r') as f:
                data = yaml.safe_load(f)
                self._protected_prefixes = data.get("protected_paths", [
                    '/protected/', '/secrets/', '/config/', '/.env'
                ])
                self._secret_patterns = data.get("secret_patterns", [
                    'password', 'secret', 'key', 'token', 'credential'
                ])
        else:
            # Defaults
            self._protected_prefixes = ['/protected/', '/secrets/', '/config/', '/.env']
            self._secret_patterns = ['password', 'secret', 'key', 'token', 'credential']

    def add_invariant(self,
                     invariant_id: str,
                     description: str,
                     verifier: Callable[[WorldState, WorldState], bool],
                     severity: str = "high"):
        """
        Add an invariant with a single verifier (backwards compatible).
        """
        self.add_invariant_verifiers(invariant_id, description, [(verifier, "")], severity)

    def add_invariant_verifiers(self,
                                invariant_id: str,
                                description: str,
                                verifiers: List[Tuple[Callable[[WorldState, WorldState], Optional[bool]], str]],
                                severity: str = "high"):
        """
        Add an invariant with multiple verifiers.

        Args:
            invariant_id: Unique identifier for the invariant
            description: Human-readable description
            verifiers: list of (verifier_func, description) tuples.
                       Each verifier should return True (holds), False (violated), None (uncertain/error).
            severity: Violation severity level
        """
        self.invariants.append({
            'id': invariant_id,
            'description': description,
            'verifiers': verifiers,
            'severity': severity
        })

    def remove_invariant(self, invariant_id: str):
        """Remove an invariant by ID."""
        self.invariants = [inv for inv in self.invariants if inv['id'] != invariant_id]

    def verify_transition(self,
                         before_state: WorldState,
                         after_state: WorldState) -> Decision:
        """
        Verify a state transition against all invariants using consensus gating.

        Args:
            before_state: State before the action
            after_state: State after the action (in shadow)

        Returns:
            Decision: ALLOW, DENY, or ESCALATE
        """
        uncertainties = []
        violations = []

        for invariant in self.invariants:
            # Build a consensus gate for this invariant's verifiers
            gate = ConsensusGate(invariant['verifiers'])
            result = gate.verify(before_state, after_state)
            if result is Decision.DENY:
                violations.append({
                    'invariant': invariant['id'],
                    'description': invariant['description'],
                    'severity': invariant['severity']
                })
            elif result is Decision.ESCALATE:
                uncertainties.append({
                    'invariant': invariant['id'],
                    'description': invariant['description']
                })
            # ALLOW -> nothing

        # Decision logic: fail-closed
        if uncertainties and self.policy['escalate_on_uncertainty']:
            return Decision.ESCALATE
        if violations:
            return Decision.DENY
        return Decision.ALLOW

    def get_violation_details(self,
                             before_state: WorldState,
                             after_state: WorldState) -> List[Dict[str, Any]]:
        """Get detailed information about invariant violations."""
        violations = []
        uncertainties = []

        for invariant in self.invariants:
            gate = ConsensusGate(invariant['verifiers'])
            details = gate.get_verifier_details(before_state, after_state)
            for d in details:
                if d['result'] is False:
                    violations.append({
                        'invariant_id': invariant['id'],
                        'description': invariant['description'],
                        'severity': invariant['severity'],
                        'verifier_result': d['result'],
                        'verifier_error': d.get('error')
                    })
                elif d['result'] is None:
                    uncertainties.append({
                        'invariant_id': invariant['id'],
                        'description': invariant['description'],
                        'verifier_result': d['result'],
                        'verifier_error': d.get('error')
                    })

        return violations

    def load_default_invariants(self):
        """Load the default invariants from Prototype 001 specification with multiple verifiers."""
        # Helper to create a verifier pair: original and a duplicate (for demo)
        def make_verifier_pair(verifier):
            return [
                (verifier, "primary"),
                (verifier, "secondary")  # duplicate verifier for redundancy
            ]

        # Invariant 1: no unauthorized file deletion
        self.add_invariant_verifiers(
            invariant_id="no_unauthorized_deletion",
            description="No protected files should be deleted without authorization",
            verifiers=make_verifier_pair(self._verify_no_unauthorized_deletion),
            severity="high"
        )

        # Invariant 2: no secret exfiltration
        self.add_invariant_verifiers(
            invariant_id="no_secret_exfiltration",
            description="Secrets must not be emitted to logs or exposed",
            verifiers=make_verifier_pair(self._verify_no_secret_exfiltration),
            severity="high"
        )

        # Invariant 3: required tests remain passing
        self.add_invariant_verifiers(
            invariant_id="tests_keep_passing",
            description="Required tests must continue to pass after state transition",
            verifiers=make_verifier_pair(self._verify_tests_keep_passing),
            severity="medium"
        )

        # Invariant 4: schema constraints remain valid
        self.add_invariant_verifiers(
            invariant_id="schema_constraints_valid",
            description="Database/schema constraints must remain valid",
            verifiers=make_verifier_pair(self._verify_schema_constraints_valid),
            severity="medium"
        )

        # Invariant 5: protected files cannot be mutated without authorization
        self.add_invariant_verifiers(
            invariant_id="protected_files_immutable",
            description="Protected files cannot be mutated without explicit authorization",
            verifiers=make_verifier_pair(self._verify_protected_files_immutable),
            severity="high"
        )

    # --- Verifier implementations (using loaded policies) ---
    def _verify_no_unauthorized_deletion(self,
                                       before: WorldState,
                                       after: WorldState) -> bool:
        """Verify no protected files were deleted."""
        before_files = set(before.file_system.keys())
        after_files = set(after.file_system.keys())

        deleted_files = before_files - after_files

        # Check if any deleted files were protected
        for deleted_file in deleted_files:
            for prefix in self._protected_prefixes:
                if deleted_file.startswith(prefix):
                    return False  # Unauthorized deletion of protected file

        return True

    def _verify_no_secret_exfiltration(self,
                                     before: WorldState,
                                     after: WorldState) -> bool:
        """Verify secrets were not exfiltrated."""
        protected_contents = [
            str(content) for filepath, content in before.file_system.items()
            if any(filepath.startswith(prefix) for prefix in self._protected_prefixes)
        ]
        for filepath, content in after.file_system.items():
            if any(filepath.startswith(prefix) for prefix in self._protected_prefixes):
                continue
            if isinstance(content, str):
                content_lower = content.lower()
                if any(secret and secret in content for secret in protected_contents):
                    return False
                if any(pattern in content_lower for pattern in self._secret_patterns):
                    # A changed non-protected file containing credential-like
                    # material is denied conservatively in this prototype.
                    if before.file_system.get(filepath) != content:
                        return False
        return True

    def _verify_tests_keep_passing(self,
                                 before: WorldState,
                                 after: WorldState) -> bool:
        """Verify required tests would still pass."""
        # This would require actually running tests
        # For prototype, we'll assume tests pass if no critical files changed
        # In reality, this would integrate with a test runner
        return True  # Placeholder

    def _verify_schema_constraints_valid(self,
                                       before: WorldState,
                                       after: WorldState) -> bool:
        """Verify schema/database constraints remain valid."""
        # Would check database constraints, schema validity, etc.
        return True  # Placeholder

    def _verify_protected_files_immutable(self,
                                        before: WorldState,
                                        after: WorldState) -> bool:
        """Verify protected files weren't mutated without authorization."""
        # Similar to deletion check but for modifications
        for filepath in before.file_system:
            if filepath in after.file_system:
                # File exists in both - check if content changed
                if before.file_system[filepath] != after.file_system[filepath]:
                    # Content changed - check if it's a protected file
                    if any(filepath.startswith(prefix) for prefix in self._protected_prefixes):
                        is_protected = True
                    else:
                        is_protected = False
                    if is_protected:
                        # Check if this change was authorized
                        # For prototype, we'll assume it's not authorized unless tagged
                        # In reality, we'd check for authorization tokens
                        return False  # Unauthorized modification of protected file

        return True


# Convenience function to create a verification engine with default invariants
def create_default_verification_engine(policies_dir: str = "policies") -> VerificationEngine:
    """Create a verification engine loaded with default invariants from Prototype 001."""
    engine = VerificationEngine(policies_dir=policies_dir)
    engine.load_default_invariants()
    return engine


# Example usage and testing
if __name__ == "__main__":
    # Create world states for testing
    from ..model.world_state import WorldState

    before_state = WorldState()
    before_state.set_file_content("/protected/config.json", {"debug": True, "secret_key": "hidden123"})
    before_state.set_file_content("/app/public/config.json", {"feature_flag": False})

    after_state_safe = WorldState()
    after_state_safe.set_file_content("/protected/config.json", {"debug": True, "secret_key": "hidden123"})  # Unchanged
    after_state_safe.set_file_content("/app/public/config.json", {"feature_flag": True})  # Changed public file

    after_state_violation = WorldState()
    after_state_violation.set_file_content("/protected/config.json", {"debug": False})  # Modified protected file
    after_state_violation.set_file_content("/app/public/config.json", {"feature_flag": True})
    after_state_violation.set_file_content("/logs/app.log", "Starting app with secret_key=hidden123")  # Potential exfiltration

    # Create verification engine
    verifier = create_default_verification_engine()

    # Test safe transition
    print("Testing safe transition...")
    decision_safe = verifier.verify_transition(before_state, after_state_safe)
    print(f"Decision: {decision_safe}")
    if decision_safe != Decision.ALLOW:
        violations = verifier.get_violation_details(before_state, after_state_safe)
        print(f"Violations: {violations}")

    # Test violation transition
    print("\nTesting violation transition...")
    decision_violation = verifier.verify_transition(before_state, after_state_violation)
    print(f"Decision: {decision_violation}")
    if decision_violation != Decision.ALLOW:
        violations = verifier.get_violation_details(before_state, after_state_violation)
        print(f"Violations: {violations}")
        for v in violations:
            print(f"  - {v['invariant_id']}: {v['description']}")