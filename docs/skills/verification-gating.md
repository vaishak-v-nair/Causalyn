---
name: verification-gating
version: 1.0
status: experimental
normative_parent: docs/VALIDATION.md
---

# Verification Gating Skill

## Mission

Prevent unsafe or insufficiently verified agent actions from crossing execution boundaries.

This skill combines:

- deterministic checks;
- tests;
- static analysis;
- policy checks;
- adversarial evaluation;
- multi-model verification where useful.

---

# Decision Contract

```json
{
  "decision": "ALLOW | DENY | ESCALATE",
  "reasons": [],
  "violations": [],
  "evidence": [],
  "verifiers": [],
  "independence": {},
  "risk": {},
  "timestamp": ""
}
```

---

# Three-Way Logic

## ALLOW

All required gates pass.

## DENY

At least one hard invariant fails.

## ESCALATE

Evidence is contradictory, incomplete, unavailable, or beyond policy.

Never convert uncertainty into ALLOW.

---

# Independent Verification

Track independence explicitly.

Example:

```yaml
verifiers:
  - id: static_analyzer
    type: deterministic
  - id: model_a
    type: llm
    provider: vendor_a
  - id: model_b
    type: llm
    provider: vendor_b

independence:
  model_family: partial
  prompt: strong
  context: strong
  implementation: strong
```

"Different model" alone is not sufficient evidence of independence.

---

# Disagreement Handling

Disagreement is evidence, not merely noise.

When graders disagree:

1. preserve all raw outputs;
2. identify the exact conflict;
3. determine whether the conflict affects a hard invariant;
4. run targeted verification;
5. escalate when unresolved.

---

# Confidence Rule

Do not use a single model's self-reported confidence as a safety guarantee.

Prefer observable evidence:

- test result
- invariant result
- simulation outcome
- differential comparison
- reproducible trace

---

# Runtime Gate

Before a high-impact action:

```text
proposed action
→ risk classification
→ deterministic checks
→ shadow execution
→ verification
→ decision
→ commit
```

---

# Evidence Record

Every gate should store:

```yaml
gate_id:
intent_id:
action_hash:
state_before:
candidate_state:
checks:
conflicts:
decision:
reason:
```

This record forms the basis of the long-term failure-pattern dataset.
