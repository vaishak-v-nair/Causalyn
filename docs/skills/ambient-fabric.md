---
name: ambient-fabric
version: 1.0
status: experimental
normative_parent: docs/ARCHITECTURE.md
---

# Ambient Fabric Skill

## Mission

Implement a state-oriented execution environment that can represent candidate system states and evaluate proposed changes before real-world commitment.

The Ambient Fabric is inspired by the VPSN concept of a continuous architectural state-space. The first engineering implementation may be discrete.

Do not pretend a discrete simulator is literally the mathematical continuum.

---

# Responsibilities

1. Ingest a baseline system state.
2. Create an isolated candidate state.
3. Apply proposed actions to the candidate state.
4. Evaluate invariants.
5. Compare baseline and candidate states.
6. Produce evidence.
7. Permit or deny commit according to policy.

---

# Minimum State Contract

```python
SystemState(
    state_id,
    parent_state_id,
    timestamp,
    resources,
    dependencies,
    invariants,
    provenance,
)
```

---

# Candidate Execution Contract

```python
CandidateRun(
    run_id,
    baseline_state_id,
    intent_id,
    actions,
    candidate_state_id,
    verification_results,
    decision,
)
```

---

# Hard Invariants

### I1 — Isolation

Candidate execution must not mutate protected production resources.

### I2 — Reproducibility

The same recorded inputs and environment should reproduce the candidate result within declared tolerances.

### I3 — Provenance

Every state mutation must identify:

- actor
- action
- source
- timestamp
- parent state

### I4 — Commit explicitness

There must be a distinct commit boundary.

---

# Shadow Execution

Preferred sequence:

```text
capture baseline
→ clone / virtualize relevant state
→ intercept action
→ execute in candidate state
→ observe result
→ verify invariants
→ decide
→ commit or discard
```

---

# VPSN Interpretation

The theoretical VPSN document describes the Ambient Fabric as a continuous manifold containing possible software states.

For the initial implementation:

`continuous manifold → finite state approximation`

This is explicitly an engineering approximation.

The objective is not to fake the manifold. The objective is to discover whether the claimed constraint/nullification behavior can be represented computationally and whether it outperforms conventional mechanisms.

---

# Failure Behavior

On:

- state divergence;
- missing dependency;
- incomplete snapshot;
- unmodeled external side effect;
- unverifiable invariant;

return:

`ESCALATE` or `DENY`.

Never silently treat missing information as a safe state.
