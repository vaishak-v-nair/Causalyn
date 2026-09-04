---
name: intent-translator
version: 1.0
status: experimental
normative_parent: docs/SYSTEM.md
---

# Intent Translator Skill

## Mission

Translate human requirements into a structured, testable Intent Specification.

This skill does not generate implementation code.

---

## Input

Natural language requirements such as:

> "Migrate the authentication service to a new architecture without breaking active sessions."

---

## Output

```yaml
intent_id: string
goal: string

scope:
  included: []
  excluded: []

required_invariants: []
forbidden_states: []

allowed_operations: []
disallowed_operations: []

security_constraints: []
data_constraints: []
availability_constraints: []

acceptance_tests: []

assumptions: []
ambiguities: []
unknowns: []
```

---

# Translation Rules

## Rule 1 — Separate goal from mechanism

Do not translate:

> "Use Kubernetes."

into an invariant.

Translate the underlying requirement:

> "The service must remain restartable across node failure."

Technology choices belong in implementation constraints.

## Rule 2 — Make vague requirements measurable

Input:

> "Make it secure."

Output must become concrete constraints, for example:

- unauthenticated requests must not access protected resources;
- secrets must not be emitted to logs;
- revoked sessions must fail authorization checks.

Never invent requirements that the user did not imply. Mark them as proposed assumptions.

## Rule 3 — Identify ambiguity

For:

> "No downtime."

record what that means:

- zero failed requests?
- zero service unavailability?
- zero data inconsistency?
- bounded latency degradation?

If undefined, record the ambiguity instead of pretending it is resolved.

## Rule 4 — Derive forbidden states

Every important requirement should produce explicit forbidden states.

Example:

```yaml
forbidden_states:
  - active_session && revoked_token
  - committed_schema_change && failed_migration
  - production_write && unverified_candidate
```

## Rule 5 — Every invariant needs a verifier

For each invariant:

```text
Invariant → Test/Checker → Observable Evidence
```

If no verifier exists:

`status: UNVERIFIED`

---

# Intent Quality Gate

Reject the Intent Specification when:

- goal is ambiguous;
- scope is undefined;
- critical invariants cannot be tested;
- destructive operations lack authorization;
- assumptions are hidden;
- acceptance criteria are missing.

---

# Anti-Slop Constraint

Never output an Intent Vector merely because it sounds mathematical.

The mathematical representation is useful only if it changes what the system can calculate, constrain, or verify.

---

# VPSN Mapping

Where appropriate:

- user goal → Intent Vector semantics
- constraints → boundary conditions
- forbidden states → paradox candidates
- invariant violation → positive κ candidate
- admissible state → low/zero κ candidate

This mapping is an implementation interpretation unless experimentally demonstrated otherwise.
