---
name: research-mode
version: 1.0
status: required
normative_parent: docs/RESEARCH.md
---

# Research Mode Skill

## Mission

Turn ambitious Epoch-V claims into falsifiable research programs.

---

# Claim Decomposition

Every major claim becomes:

```text
Claim
→ Mechanism
→ Necessary assumptions
→ Baseline
→ Prediction
→ Experiment
→ Metric
→ Falsification condition
```

---

# Example

Claim:

> VPSN-inspired constraint dynamics can reduce execution failures.

Mechanism:

> Candidate states are mapped into a constraint representation and iteratively transformed toward lower violation energy.

Baseline:

> ordinary plan → execute → test → repair

Experiment:

> identical tasks, identical resource budget, compare systems.

Metrics:

- task success rate
- invariant violation rate
- recovery count
- runtime
- compute cost
- catastrophic failure rate

Falsification:

> no statistically meaningful improvement over baseline, or worse reliability at equal cost.

---

# Evidence Standards

Strong:

- reproducible benchmark;
- independent replication;
- real-system evaluation;
- formally verified property;
- source-backed fact.

Weak:

- anecdotal success;
- single demonstration;
- generated example;
- model confidence;
- architectural intuition.

Never confuse weak evidence with proof.

---

# Research Log Requirement

For every experiment record:

- hypothesis;
- exact environment;
- code version;
- dataset/input;
- parameters;
- baseline;
- results;
- failures;
- interpretation;
- next experiment.

---

# Anti-Confirmation Bias

Agents must actively search for evidence that would disprove the design.

Ask:

> What experiment would make this architecture obviously wrong?

Run that experiment early.
