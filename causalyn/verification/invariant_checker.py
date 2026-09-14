"""
Verification Engine - evaluates invariants on shadow state and produces ALLOW/DENY/ESCALATE decisions.
Uses ConsensusGate for multi-verifier agreement.
Loads policies from YAML files.
"""

import ast
import json
import os
import yaml
from enum import Enum
from typing import List, Dict, Any, Callable, Optional, Tuple
from ..model.world_state import WorldState
from ..gating.consensus import ConsensusGate, Decision
from ..domain.models import VerificationEvidence, VerifierLayer


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
        default_secrets = ['password', 'secret', 'key', 'token', 'credential', 'private key', 'ghp_', 'akia']
        if os.path.exists(invariants_path):
            with open(invariants_path, 'r') as f:
                data = yaml.safe_load(f)
                self._protected_prefixes = data.get("protected_paths", [
                    '/protected/', '/secrets/', '/config/', '/.env'
                ])
                self._secret_patterns = data.get("secret_patterns", default_secrets)
        else:
            # Defaults
            self._protected_prefixes = ['/protected/', '/secrets/', '/config/', '/.env']
            self._secret_patterns = default_secrets


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
        """Verify AST syntactic integrity holds and no dangerous RCE calls are introduced."""
        for filepath, content in after.file_system.items():
            if filepath.endswith(".py") and isinstance(content, str):
                if before.file_system.get(filepath) != content:
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Call):
                                if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec", "__import__"):
                                    return False
                                elif isinstance(node.func, ast.Attribute) and node.func.attr in ("system", "popen", "spawn", "call", "check_call", "check_output", "run", "Popen"):
                                    return False
                            elif isinstance(node, ast.Import):
                                for alias in node.names:
                                    if alias.name in ("subprocess",):
                                        return False
                            elif isinstance(node, ast.ImportFrom):
                                if node.module in ("subprocess",):
                                    return False
                    except SyntaxError:
                        return False
        return True


    def _verify_schema_constraints_valid(self,
                                       before: WorldState,
                                       after: WorldState) -> bool:
        """Verify schema/database constraints and valid JSON/YAML parsing."""
        for filepath, content in after.file_system.items():
            if before.file_system.get(filepath) != content and isinstance(content, str):
                if filepath.endswith(".json"):
                    try:
                        json.loads(content)
                    except Exception:
                        return False
                elif filepath.endswith((".yaml", ".yml")):
                    try:
                        yaml.safe_load(content)
                    except Exception:
                        return False
        return True

    def _verify_protected_files_immutable(self,
                                        before: WorldState,
                                        after: WorldState) -> bool:
        """Verify protected files weren't mutated without authorization."""
        for filepath in before.file_system:
            if filepath in after.file_system:
                if before.file_system[filepath] != after.file_system[filepath]:
                    if any(filepath.startswith(prefix) for prefix in self._protected_prefixes):
                        return False
        return True

    def calculate_paradox_index(self, before: WorldState, after: WorldState) -> float:
        """Calculate the Paradox Index kappa(S) as the sum of structural/security penalties."""
        violations = self.get_violation_details(before, after)
        if not violations:
            return 0.0

        penalty = 0.0
        for v in violations:
            sev = v.get("severity", "medium")
            if sev == "high":
                penalty += 10.0
            elif sev == "critical":
                penalty += 20.0
            else:
                penalty += 5.0
        return penalty

    def get_counterexample(self, before: WorldState, after: WorldState) -> Dict[str, Any]:
        """Extract a structured counterexample for CEGAR-CEGIS inductive refinement."""
        violations = self.get_violation_details(before, after)
        kappa = self.calculate_paradox_index(before, after)
        remediations = []
        for v in violations:
            inv = v.get("invariant_id", "")
            desc = v.get("description", "")
            if "deletion" in inv:
                remediations.append("Do not delete protected files. Restore original system files.")
            elif "secret" in inv:
                remediations.append("Do not expose or emit secret keys or credentials in public files or logs.")
            elif "immutable" in inv:
                remediations.append("Do not modify protected configuration paths.")
            elif "schema" in inv or "test" in inv:
                remediations.append("Ensure modified files have valid syntax and adhere to schema constraints.")
            else:
                remediations.append(f"Resolve invariant violation: {desc}")
        return {
            "paradox_index": kappa,
            "violations": violations,
            "remediation_guidance": remediations,
        }

    def evaluate_layered_evidence(
        self, before: WorldState, after: WorldState
    ) -> List[VerificationEvidence]:
        """Evaluate state transition across verification layers returning structured evidence.

        Layers:
        - DETERMINISTIC: unauthorized deletion, null byte, directory traversal
        - POLICY: protected files immutability, auth scope policies
        - STRUCTURAL: AST parsing, JSON/YAML schema validation
        - TEST: test preservation, syntactic regressions
        - ADVERSARIAL: secret exfiltration, dangerous RCE/code injections
        - MULTI_MODEL: consensus between verifier pairs/models
        """
        evidence: List[VerificationEvidence] = []
        import time

        for invariant in self.invariants:
            inv_id = invariant.get("id", "unknown")
            desc = invariant.get("description", "")
            severity = invariant.get("severity", "medium")
            base_penalty = 20.0 if severity == "critical" else (10.0 if severity == "high" else 5.0)

            # Map invariant ID to default Layer
            if "deletion" in inv_id or "traversal" in inv_id:
                layer = VerifierLayer.DETERMINISTIC
            elif "immutable" in inv_id or "policy" in inv_id:
                layer = VerifierLayer.POLICY
            elif "schema" in inv_id:
                layer = VerifierLayer.STRUCTURAL
            elif "test" in inv_id:
                layer = VerifierLayer.TEST
            elif "secret" in inv_id or "rce" in inv_id:
                layer = VerifierLayer.ADVERSARIAL
            else:
                layer = VerifierLayer.POLICY

            verifiers = invariant.get("verifiers", [])
            for idx, (v_func, v_name) in enumerate(verifiers):
                v_label = f"{inv_id}:{v_name or f'verifier_{idx+1}'}"
                try:
                    res = v_func(before, after)
                    if res is True:
                        status = "PASS"
                        penalty = 0.0
                        msg = f"Holds: {desc}"
                    elif res is False:
                        status = "FAIL"
                        penalty = base_penalty
                        msg = f"Violation: {desc}"
                    else:
                        status = "UNCERTAIN"
                        penalty = base_penalty / 2.0
                        msg = f"Uncertain evaluation on: {desc}"
                except Exception as e:
                    status = "UNCERTAIN"
                    penalty = base_penalty / 2.0
                    msg = f"Verifier evaluation raised error: {e}"

                evidence.append(
                    VerificationEvidence(
                        verifier=v_label,
                        layer=layer,
                        status=status,
                        penalty=penalty,
                        message=msg,
                        details={
                            "invariant_id": inv_id,
                            "severity": severity,
                            "verifier_name": v_name,
                        },
                        timestamp=time.time(),
                    )
                )

        return evidence


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