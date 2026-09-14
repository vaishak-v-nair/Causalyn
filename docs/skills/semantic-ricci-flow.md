---
name: semantic-ricci-flow
version: 1.0
status: research
normative_parent: docs/VPSN_BRIDGE.md
---

# Semantic Ricci Flow Skill

## Mission

Investigate and implement the proposed VPSN-inspired flow:

∂gᵢⱼ / ∂τ = −2Rᵢⱼ + ∇ᵢ∇ⱼ I

The first engineering goal is not to claim that software literally evolves according to Ricci flow.

The goal is to determine whether a geometry-inspired optimization process can encode system constraints and reliably move candidate states toward admissible regions.

---

# Required Definitions

Before implementation, define:

- state manifold approximation;
- metric `g`;
- curvature term `R`;
- intent field `I`;
- parameter/time variable `τ`;
- boundary conditions;
- admissible state;
- convergence criterion;
- divergence criterion.

---

# Engineering Representation

A practical prototype may use:

```text
software state
   ↓
feature/state embedding
   ↓
constraint geometry
   ↓
energy / tension function
   ↓
iterative update
   ↓
candidate state
   ↓
invariant verification
```

This is an implementation analogue, not proof of the full VPSN mathematics.

---

# Nullification Model

The theory proposes invalid states decay toward zero.

A prototype must define exactly what "zero" means.

Examples:

- constraint violation score = 0
- residual error = 0
- policy violation count = 0
- objective loss below tolerance

Do not use "zero" rhetorically.

---

# Required Experiments

For every solver version measure:

- initial constraint violation;
- final constraint violation;
- convergence rate;
- runtime;
- failure rate;
- local minima;
- oscillation;
- sensitivity to initialization;
- sensitivity to noisy intent;
- adversarial cases.

---

# Falsification Conditions

The hypothesis is weakened or rejected if:

- the solver does not converge reliably;
- the resulting state violates hard invariants;
- conventional search performs better at equal budget;
- small intent changes cause unstable state changes;
- the mathematical abstraction provides no practical predictive advantage.

Failures are first-class results.

---

# Prohibited Claims

Do not claim:

> "The equation proves software correctness."

The supported statement is:

> "The prototype evaluates whether a Ricci-flow-inspired optimization mechanism can enforce defined software constraints."

That is the research question.
