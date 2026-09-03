"""
Intent Translator - translates human requirements into structured Intent Specification.
Based on the intent-translator skill.
"""

import re
import yaml
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class IntentSpecification:
    """Structured representation of human intent."""
    intent_id: str
    goal: str

    scope: Dict[str, List[str]] = field(default_factory=lambda: {
        "included": [],
        "excluded": []
    })

    required_invariants: List[str] = field(default_factory=list)
    forbidden_states: List[str] = field(default_factory=list)

    allowed_operations: List[str] = field(default_factory=list)
    disallowed_operations: List[str] = field(default_factory=list)

    security_constraints: List[str] = field(default_factory=list)
    data_constraints: List[str] = field(default_factory=list)
    availability_constraints: List[str] = field(default_factory=list)

    acceptance_tests: List[str] = field(default_factory=list)

    assumptions: List[str] = field(default_factory=list)
    ambiguities: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)

    def to_yaml(self) -> str:
        """Convert to YAML format."""
        return yaml.dump(self.__dict__, default_flow_style=False)

    def to_json(self) -> str:
        """Convert to JSON format."""
        return json.dumps(self.__dict__, indent=2)


class IntentTranslator:
    """Translates natural language requirements into Intent Specifications."""

    def __init__(self):
        self.intent_counter = 0

    def translate(self, natural_language: str) -> IntentSpecification:
        """
        Translate natural language requirements into a structured Intent Specification.

        Args:
            natural_language: The human requirements in natural language

        Returns:
            IntentSpecification: Structured representation of the intent
        """
        self.intent_counter += 1
        intent_id = f"intent-{self.intent_counter:03d}"

        # Initialize the spec
        spec = IntentSpecification(
            intent_id=intent_id,
            goal=self._extract_goal(natural_language)
        )

        # Apply translation rules
        self._apply_rule_1_separate_goal_from_mechanism(natural_language, spec)
        self._apply_rule_2_make_vague_measurable(natural_language, spec)
        self._apply_rule_3_identify_ambiguity(natural_language, spec)
        self._apply_rule_4_derive_forbidden_states(natural_language, spec)
        self._apply_rule_5_every_invariant_needs_verifier(natural_language, spec)

        # Apply anti-slop constraint
        self._apply_anti_slop_constraint(spec)

        # Apply VPSN mapping (where appropriate)
        self._apply_vpsn_mapping(natural_language, spec)

        return spec

    def _extract_goal(self, text: str) -> str:
        """Extract the goal from natural language text."""
        # Simple heuristic: look for action verbs and objectives
        # In a real implementation, this would be more sophisticated
        text_lower = text.lower()

        # Common goal patterns
        if "migrate" in text_lower:
            return "Migrate the authentication service to a new architecture"
        elif "build" in text_lower or "create" in text_lower:
            return "Build a new system or component"
        elif "fix" in text_lower or "resolve" in text_lower:
            return "Fix an existing issue"
        elif "improve" in text_lower or "enhance" in text_lower:
            return "Improve or enhance existing functionality"
        else:
            # Default: extract first sentence or reasonable length
            sentences = re.split(r'[.!?]+', text)
            if sentences and len(sentences[0].strip()) > 10:
                return sentences[0].strip()
            return text[:100].strip() + ("..." if len(text) > 100 else "")

    def _apply_rule_1_separate_goal_from_mechanism(self, text: str, spec: IntentSpecification):
        """Rule 1: Separate goal from mechanism - don't translate tech choices into invariants."""
        # This is more of a principle than an algorithmic step
        # In practice, we'd need NLP to detect technology mentions and avoid making them invariants
        pass

    def _apply_rule_2_make_vague_measurable(self, text: str, spec: IntentSpecification):
        """Rule 2: Make vague requirements measurable."""
        text_lower = text.lower()

        # Handle common vague requirements
        if "secure" in text_lower or "security" in text_lower:
            spec.security_constraints.extend([
                "Unauthenticated requests must not access protected resources",
                "Secrets must not be emitted to logs",
                "Revoked sessions must fail authorization checks"
            ])

        if "fast" in text_lower or "performance" in text_lower:
            spec.data_constraints.append("Response time must be under 2 seconds for 95% of requests")

        if "reliable" in text_lower or "reliability" in text_lower:
            spec.availability_constraints.append("System must maintain 99.9% uptime")

    def _apply_rule_3_identify_ambiguity(self, text: str, spec: IntentSpecification):
        """Rule 3: Identify ambiguity."""
        text_lower = text.lower()

        ambiguities = []

        if "no downtime" in text_lower:
            ambiguities.extend([
                "Does 'no downtime' mean zero failed requests?",
                "Or zero service unavailability?",
                "Or zero data inconsistency?",
                "Or bounded latency degradation?"
            ])

        if "scalable" in text_lower:
            ambiguities.append("What does 'scalable' mean? More users? More data? Higher throughput?")

        spec.ambiguities.extend(ambiguities)

    def _apply_rule_4_derive_forbidden_states(self, text: str, spec: IntentSpecification):
        """Rule 4: Derive forbidden states from requirements."""
        text_lower = text.lower()

        # Example forbidden states based on common requirements
        if "migration" in text_lower or "update" in text_lower:
            spec.forbidden_states.extend([
                "active_session && revoked_token",
                "committed_schema_change && failed_migration",
                "production_write && unverified_candidate"
            ])

        if "security" in text_lower or "secure" in text_lower:
            spec.forbidden_states.extend([
                "unauthenticated_access && protected_resource",
                "secret_emission && logs"
            ])

    def _apply_rule_5_every_invariant_needs_verifier(self, text: str, spec: IntentSpecification):
        """Rule 5: Every invariant needs a verifier - mark unverifiable ones as UNVERIFIED."""
        # For each invariant we've added, we would normally check if a verifier exists
        # For now, we'll just note that verification needs to be implemented
        pass

    def _apply_anti_slop_constraint(self, spec: IntentSpecification):
        """Anti-Slop Constraint: Never output an Intent Vector merely because it sounds mathematical."""
        # Ensure we're not adding mathematical formulations without purpose
        # This is more of a guideline - in practice we'd review the spec for unnecessary math
        pass

    def _apply_vpsn_mapping(self, text: str, spec: IntentSpecification):
        """VPSN Mapping: Map concepts to VPSN terminology where appropriate."""
        text_lower = text.lower()

        # Only apply VPSN mapping if we're dealing with relevant concepts
        if any(term in text_lower for term in ["state", "system", "behavior", "migration", "update"]):
            # Map user goal to Intent Vector semantics (already done in goal extraction)
            # Map constraints to boundary conditions (done in constraints)
            # Map forbidden states to paradox candidates (done in forbidden_states)
            # In a full implementation, we'd add VPSN-specific fields
            pass


def translate_intent(natural_language: str) -> str:
    """
    Convenience function to translate natural language to YAML intent specification.

    Args:
        natural_language: Human requirements in natural language

    Returns:
        YAML string representation of the intent specification
    """
    translator = IntentTranslator()
    spec = translator.translate(natural_language)
    return spec.to_yaml()


# Example usage
if __name__ == "__main__":
    example_requirement = """
    Migrate the authentication service to a new architecture without breaking active sessions.
    Make it secure and ensure no downtime during the migration.
    """

    spec = IntentTranslator().translate(example_requirement)
    print("Generated Intent Specification:")
    print(spec.to_yaml())