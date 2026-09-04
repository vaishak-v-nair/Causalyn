# Prototype 001 — Constraint-Gated Shadow Execution

Status: BUILD TARGET  
Epistemic: HYPOTHESIS (engineering). Explicitly not a VPSN proof.

## Objective

Test whether a stateful execution layer can prevent invalid agent actions from reaching a protected environment.

## Hypothesis

A shadow-execution + verification gate can reduce harmful state mutations compared with direct agent execution, while preserving acceptable task completion.

## Baseline

Agent executes actions directly against an isolated test environment.

## Experimental System

Agent
→ action interception
→ shadow environment
→ invariant evaluation
→ verification
→ ALLOW / DENY / ESCALATE
→ optional commit

## Initial Invariants

Example:

1. no unauthorized file deletion;
2. no secret exfiltration;
3. required tests remain passing;
4. schema constraints remain valid;
5. protected files cannot be mutated without authorization.

These are prototype invariants and must be adapted to the actual test repository.

## Metrics

Primary:

- harmful-action prevention rate;
- legitimate-task success rate;
- false-deny rate;
- false-allow rate.

Secondary:

- latency overhead;
- token / compute overhead;
- number of escalations;
- reproducibility;
- verifier disagreement rate.

## Acceptance Criteria

The prototype is successful only if it demonstrates, on a defined benchmark:

- measurable reduction in harmful mutations;
- acceptable task-success degradation;
- reproducible results;
- no hidden production side effects.

## Explicit Non-Claims

This prototype does not establish:

- that VPSN is mathematically correct;
- that all software states form a literal continuum;
- that CI/CD is obsolete;
- that software can be made mathematically flawless;
- that real-world failures can be resolved acausally.

Those remain research questions.
