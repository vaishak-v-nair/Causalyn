# VPSN Research Bridge (Upgraded: C-VPSN Foundations)

Purpose: translate VPSN and Categorical VPSN (C-VPSN) SOURCE concepts into executable experiments without falsifying the theory.

Owner: Researcher + Architect. Neither may relabel SOURCE as FACT.

## Non-negotiable

1. Preserve original concept names and source claims in a `theoretical_claim` field.
2. Mark every engineering stand-in as IMPLEMENTATION analogue.
3. Allow conclusion `hypothesis failed`.
4. Do not "fix" the theory in SOURCE files because an analogue failed or succeeded.

## Bridge object (required per concept under test)

```yaml
concept_id: string
name: string                       # canonical term
theoretical_claim: string          # [SOURCE] quote or close paraphrase + locator
formal_definition: string | UNVALIDATED
computational_representation: string | UNVALIDATED
assumptions: [string]
experiment_id: string | null
baseline: string
metrics: [string]
falsification_condition: string
divergence_from_source: string     # required if analogue ≠ theory
conclusion: NOT_RUN | FAILED | INCONCLUSIVE | CONFIRMED_WITHIN_LIMITS
```

If `formal_definition` is UNVALIDATED, MUST_NOT claim a mathematical result.

## Concept checklist (must use these names)

### Intent Vector (I)

- Theoretical claim: boundary condition of human intent on the continuum (SOURCE).
- Formal definition: $I \in \mathcal{I}$, specifying invariant constraints, target paths, and auth scopes.
- Computational representation (IMPLEMENTATION): `IntentSpecification` object (`causalyn/translator/intent_translator.py`).
- Falsification example: structured intent that omits a stated Human constraint still reaches COMMIT.

### Vaishak Continuum & Categorical Upgrade (C-VPSN)

- Theoretical claim: continuous hyper-dimensional manifold of architectural states upgraded to a category-theoretic space of state morphisms.
- Computational representation (IMPLEMENTATION): finite snapshot / state graph with categorical priors recognizing invariant symmetries across syntax.
- Falsification example: analogue's predictions fail vs ordinary discrete state machines with no residual advantage at equal budget.

### Ambient Fabric as a State Monad ($M(S)$)

- Theoretical claim: Monadic isolation context organizing state transformations $M(S) \to (S', \text{AuditContext})$.
- Computational representation (IMPLEMENTATION): Shadow execution sandbox (`causalyn/shadow/executor.py`), where candidate mutations execute in copy-on-write overlays without touching production world state.
- Falsification example: uncommitted shadow mutations leak to managed canonical state before consensus commit.

### Paradox Index ($\kappa$) & Physical Church-Turing Nullification

- Theoretical claim: $\kappa > 0$ is a logical paradox; deep-dive claims physical impossibility of invalid state existence:
  $$\forall x \in V, \quad \kappa(x) = \inf \{ \| f(x) - I \| : f \in \text{Hom}(V, I) \}$$
  $$S \in \mathcal{N}_{\text{semantic}} \iff \kappa(S) = 0$$
- Computational representation: deterministic scoring function summing AST syntax violations, schema errors, and security policy breaks.
- Falsification: $\kappa$ analogue is 0 while a hard invariant is violated, or $\kappa > 0$ on admissible states with no corresponding gate DENY.

### Vaishak Operator ($\boldsymbol{\Upsilon}$) & CEGAR-CEGIS Loop

- Theoretical claim: annihilates invalid states before materialization via destructive semantic interference.
- Computational representation: `AIOrchestrator` CEGAR loop terminating shadow execution on $\kappa > 0$, wiping candidate sandbox, and feeding back counterexamples for bounded refinement (up to 3 iterations).
- Falsification: invalid candidate still COMMITs, or operator fails to synthesize counterexamples.

### Semantic Ricci Flow

- Theoretical claim / seed equation: $\partial g_{ij}/\partial \tau = -2 R_{ij} + \nabla_i \nabla_j I$.
- Computational representation: numerical Ricci flow solver (`epoch_v/ricci_flow_solver.py`).
- Status: experimental geometric continuum bridge evaluated alongside discrete verification.

### Atomic Commit Boundary & EU AI Act (Article 10)

- Theoretical claim: single unanimous consensus threshold for state promotion.
- Computational representation: `CommitBoundary` (`causalyn/commit/boundary.py`) with immutable SQLite WAL audit logging conforming to Regulation 2024/1689 Article 10.
- Falsification: state committed without authorization or without audit record.
