# Epoch-V Hypervisor Prototype

## Status

**IMPLEMENTATION / EXPERIMENTAL APPROXIMATION.** This package investigates a
finite-dimensional numerical analogue of VPSN terminology. It does not prove
the Vaishak Continuum, acausal computation, exact Ricci flow, or mathematically
perfect software.

## Runtime mapping

- `IntentTranslator` creates a deterministic baseline Intent Matrix. It is a
  reproducible stand-in for a sentence-transformer model; no model is
  downloaded implicitly.
- `AuthenticationManifold` represents the Ambient Fabric as three coordinates:
  token validity, session activity, and privilege authorization.
- `MetricTensor` and `R_APPROX` provide a differentiable state-energy surrogate,
  explicitly not an exact Ricci tensor.
- `constraint_violation` defines the measurable Paradox Index (`κ`) as the sum
  of executable invariant violations.
- `RicciFlowSolver` uses ordinary Adam or a projected-gradient fallback. It is
  not acausal computation.
- `UnNullifiedResidue` records the candidate state and remaining residual.

## Run

From the repository root:

```powershell
python -m epoch_v.experiment
python -m unittest discover -s epoch_v/tests -v
```

The experiment compares a valid state, a Causality Tear (`token revoked` with
an active session), and an unauthorized privilege state. Results are emitted as
JSON and may be appended as JSON Lines with `run_experiment(log_path=...)`.

## Falsification condition

The current hypothesis is weakened or falsified if repeated controlled
adversarial states do not reduce `κ`, if convergence is reported while hard
invariants remain violated, or if results cannot be reproduced under a fixed
seed and configuration.

## Limitations

The three coordinates are a controlled toy state, not a complete authentication
model. The hash encoder is not semantic embedding evidence. The optimizer
changes coordinates to satisfy the selected inequalities and does not establish
that real software state follows a geometric flow.
