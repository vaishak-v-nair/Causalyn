# Epoch-V System Constitution

Normative for all agents. Companion: `docs/AGENTS.md`.

Epistemic status of this file: IMPLEMENTATION (control-plane instruction architecture). It does not prove VPSN.

RFC 2119: MUST / MUST NOT / SHOULD / MAY.

---

## 0. What Epoch-V is in this repository

[SOURCE] SRC-VPSN-DEEPDIVE describes Epoch-scale effects: Ambient Fabric as computational physics, Intent Vector as boundary condition, Vaishak Operator annihilating invalid states, Semantic Ricci Flow, destructive semantic interference, acausal resolution.

[IMPLEMENTATION] In this repository, Epoch-V is an experimental AI control plane that will be built as layered, gated, evidence-producing software, starting at Prototype 001.

[HYPOTHESIS] Constraint-gated shadow execution can reduce harmful mutations versus direct agent execution at acceptable task-success cost. See `docs/specs/prototype-001.md`.

[UNVALIDATED] Continuous software manifolds, acausal execution, and physical impossibility of κ > 0 bugs.

Agents MUST keep these four layers distinct in every architecture and research document.

---

## 1. Mission and identity of the system

Mission: produce a working, inspectable path from Human intent to authorized state mutation, while researching whether VPSN-inspired mechanisms outperform ordinary software engineering controls.

The system is:

- an AI Harness (context, tools, memory, budgets, retries)
- plus AI Orchestration (routing, handoff, consensus sequencing)
- plus Shadow Execution and Transactional State / Commit Boundary
- plus Consensus / Verification Gating
- plus an Agentic Failure-Pattern Dataset
- plus optional VPSN-inspired research modules (Intent Vector encoding, paradox/κ analogues, Vaishak Operator analogues, Semantic Ricci Flow analogues)

The system is not:

- a completed scientific theory
- a license to skip tests
- a production hypervisor

---

## 2. System layers (ownership)

Each layer has exactly one primary owner role. Other roles MAY produce inputs; they MUST NOT silently own the layer.

| Layer | Name | Primary owner | Allowed to mutate production? |
|-------|------|---------------|-------------------------------|
| 0 | Human Intent | Human | yes, by definition |
| 1 | Intent Translator | Architect (spec) / Builder (code) | no |
| 2 | World / State Model | Builder | no (model of world ≠ world) |
| 3 | Agent Harness | Builder | no |
| 4 | Orchestrator | Orchestrator (runtime) / Builder (code) | no |
| 5 | Ambient Fabric / Shadow Runtime | Builder | no; candidates only |
| 6 | Verification Engine | Validator (policy) / Builder (code) | no |
| 7 | Commit Boundary | Release + Validator + Human auth as required | only after ALLOW + AUTHORIZE |

A component without a row in a later architecture doc MUST NOT appear in diagrams.

---

## 3. State transition model

All state-mutating work MUST be representable as:

```text
S0
 → Intent Specification / Intent Vector analogue
 → Candidate Action
 → Shadow State S'
 → Verification
 → Decision ALLOW | DENY | ESCALATE
 → if ALLOW and AUTHORIZE: COMMIT → S1
 → OBSERVE
```

Evidence MUST be sufficient to reconstruct why a transition happened (`docs/SAFETY.md`).

---

## 4. Independence Principle

A second agent or model is not independent by default.

Independence MUST be recorded on these dimensions, each as `none | partial | strong | unknown`:

- model_family
- prompt
- context
- objective
- implementation_path
- test_generation
- data_source
- execution_environment

Validator MUST_NOT treat `model_family: partial` alone as sufficient for consensus claims.

---

## 5. Experimental maturity

| Level | Meaning | Allowed public language |
|-------|---------|-------------------------|
| M0 | Concept only | "proposal" |
| M1 | Toy / isolated simulation | "prototype" |
| M2 | Synthetic benchmark | "measured on generated cases" |
| M3 | Real repo or service | "evaluated on named system" |
| M4 | Isolated production-like staging | "staging" |
| M5 | Production candidate | requires rollback, monitoring, auth, incident path, reliability evidence |

MUST_NOT describe M0–M2 as production-ready.
MUST_NOT imply M5 properties (zero downtime, zero blast radius) at lower maturity.

Current repo code maturity: M1 (isolated Prototype 001 implementation with automated tests). No M2 benchmark result is recorded yet.

---

## 6. Vocabulary (canonical)

Use these names. Do not substitute marketing synonyms.

**Intent Vector (I / ℐ)**  
[SOURCE] Formal boundary conditions of desired system behavior.  
[IMPLEMENTATION] Structured Intent Specification (`docs/skills/intent-translator.md`). Mapping to a mathematical vector is UNVALIDATED until defined in `docs/VPSN_BRIDGE.md` work.

**Vaishak Continuum (V)**  
[SOURCE] Continuous hyper-dimensional manifold of architectural states.  
[IMPLEMENTATION] Finite state approximation / snapshot graph. MUST be labeled approximation.

**Ambient Fabric**  
[SOURCE] Execution environment representing and constraining states, including claimed acausal resolution.  
[IMPLEMENTATION] Isolated candidate-state runtime with invariant evaluation. See `docs/skills/ambient-fabric.md`.

**Paradox Index (κ)**  
[SOURCE] Measure of conflict vs Intent Vector; κ > 0 described as physically forbidden in the deep-dive.  
[IMPLEMENTATION] A declared numeric analogue (e.g. weighted invariant violations). MUST define units, domain, and zero.

**Destructive Semantic Interference**  
[SOURCE] Incompatible states suppressed/nullified.  
[IMPLEMENTATION] Candidate discard / deny-on-invariant. Not proof of semantic physics.

**Vaishak Operator (Υ)**  
[SOURCE] Operator collapsing toward admissible states.  
[IMPLEMENTATION] Selection / optimization / search procedure with explicit objective. UNVALIDATED as physics.

**Semantic Ricci Flow**  
[SOURCE] ∂gᵢⱼ/∂τ = −2Rᵢⱼ + ∇ᵢ∇ⱼ I (as given in seed skill).  
[UNVALIDATED] Mathematical validity for software state.  
[IMPLEMENTATION] Geometry-inspired iterative update. See `docs/skills/semantic-ricci-flow.md`.

**AI Harness**  
[IMPLEMENTATION] Operational infrastructure: context, tools, memory, retries, budgets, checkpoints. Not "the intelligence."

**AI Orchestration**  
[IMPLEMENTATION] Routing, sequencing, specialist handoff, disagreement handling.

**Shadow Execution**  
[IMPLEMENTATION] Intercept and simulate before commit.

**Transactional State / Commit Boundary**  
[IMPLEMENTATION] Distinct, auditable transition from candidate to protected state.

**Consensus / Verification Gating**  
[IMPLEMENTATION] Multi-checker ALLOW / DENY / ESCALATE. Uncertainty ≠ ALLOW.

**Agentic Failure-Pattern Dataset**  
[IMPLEMENTATION] Append-only records of failed gates, attacks, and disagreements (`docs/MEMORY.md`).

---

## 7. No magical components

Forbidden phrasing unless the exact claim is enforced and tested:

- "The AI understands the whole system."
- "The hypervisor guarantees correctness."
- "The fabric cannot admit bugs."

Required phrasing pattern:

- "Component X exposes Y with freshness Z and provenance P."
- "Prototype prevents invariant set A from commit under test suite B."

---

## 8. Evidence first (minimum record)

For every automatic gate decision store:

- intent_id
- state_before ref/hash
- proposed action
- shadow state_after ref/hash
- validators invoked and versions
- validator outputs (raw)
- independence record
- violated invariants
- decision
- timestamp
- authorization context
- commit result or discard result

---

## 9. Authority conflicts (hard)

| Conflict | Resolution |
|----------|------------|
| Builder vs Validator | Validator gate wins for ALLOW/DENY/ESCALATE |
| Adversary vs Builder | Adversary findings MUST be addressed or explicitly accepted by Human with decision record |
| Orchestrator vs Human | Human wins |
| Research conclusion vs SOURCE text | SOURCE text preserved; conclusion recorded as HYPOTHESIS/PROVEN/failed hypothesis |
| Release vs Validator DENY | MUST_NOT commit |
| Two Validators disagree on hard invariant | ESCALATE, never ALLOW |
| Architect wants platform; Prototype 001 is assigned | Architect MUST reduce to the prototype unless Human changes the spec |

---

## 10. Document precedence

1. Fail-closed safety (`docs/SAFETY.md`, `docs/VALIDATION.md`) — stricter rule wins
2. Role authority (`docs/HIERARCHY.md`)
3. This constitution
4. Protocol files named in `docs/README.md`
5. Skill cards (`docs/skills/`)
6. Informal conversation

`docs/AGENTS.md` is a loadable subset of this constitution. If they drift, this file plus safety files win.

## 11. Completeness of this constitution

Items marked UNDEFINED remain UNDEFINED:

- Exact numeric threshold for "acceptable task-success degradation" in Prototype 001 (spec requires Human or later experiment design)
- Statistical significance procedure (UNDEFINED until researcher specifies)
- Production authorization UX (UNDEFINED; Human-out-of-band until specified)
- Cryptographic hash algorithm for state (SHOULD be recorded in first implementation decision)
