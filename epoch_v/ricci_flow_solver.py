from dataclasses import dataclass
from enum import Enum
from typing import Any
from .constraints import check_invariants, constraint_violation, constraint_violations
from .paradox_index import paradox_index
from .residue import UnNullifiedResidue

try:
    import torch
    _TORCH = True
except ImportError:
    torch = None
    _TORCH = False

class SolverStatus(Enum):
    CONVERGED = "CONVERGED"
    DIVERGED = "DIVERGED"
    MAX_STEPS = "MAX_STEPS"
    UNSATISFIABLE = "UNSATISFIABLE"
    NUMERICALLY_UNSTABLE = "NUMERICALLY_UNSTABLE"

@dataclass(frozen=True)
class SolverResult:
    final_state: tuple
    initial_kappa: float
    final_kappa: float
    steps: int
    status: SolverStatus
    constraint_results: dict
    metrics: dict
    limitations: tuple = ("R_APPROX is diagonal state-energy, not exact Ricci curvature",
                          "κ is an invariant-violation analogue")

    @property
    def residue(self) -> UnNullifiedResidue:
        return UnNullifiedResidue(self.final_state, self.initial_kappa, self.final_kappa,
                                  self.steps, self.status.value, constraint_violations(self.final_state), self.metrics)

class RicciFlowSolver:
    def __init__(self, config=None):
        from .config import RuntimeConfig
        self.config = config or RuntimeConfig()

    def solve(self, fabric: Any, intent: Any = None) -> SolverResult:
        initial = constraint_violation(fabric)
        if _TORCH and hasattr(fabric, "state"):
            # Optimizer is intentionally ordinary optimization, not acausal computation.
            optimizer = torch.optim.Adam([fabric.state], lr=self.config.learning_rate)
            for step in range(1, self.config.max_steps + 1):
                optimizer.zero_grad()
                token, session, privilege = fabric.state
                energy = self.config.rigidity_strength * (
                    torch.relu(session-token)**2 + torch.relu(session-privilege)**2)
                energy += torch.sum(torch.relu(-fabric.state)**2 + torch.relu(fabric.state-1)**2)
                energy.backward(); optimizer.step()
                with torch.no_grad(): fabric.state.clamp_(0, 1)
                current = constraint_violation(fabric)
                if not torch.isfinite(fabric.state).all(): return self._result(fabric, initial, step, SolverStatus.NUMERICALLY_UNSTABLE)
                if current > self.config.stability_threshold:
                    return self._result(fabric, initial, step, SolverStatus.DIVERGED)
                if current <= self.config.convergence_threshold:
                    return self._result(fabric, initial, step, SolverStatus.CONVERGED)
            return self._result(fabric, initial, self.config.max_steps, SolverStatus.MAX_STEPS)
        # Dependency-free deterministic projected gradient fallback.
        state = list(fabric.state)
        for step in range(1, self.config.max_steps + 1):
            token, session, privilege = state
            if session > token:
                state[1] -= self.config.learning_rate * self.config.rigidity_strength * (session-token)
            if session > privilege:
                state[1] -= self.config.learning_rate * self.config.rigidity_strength * (session-privilege)
            state = [min(1.0, max(0.0, x)) for x in state]; fabric.state = state
            if constraint_violation(state) > self.config.stability_threshold:
                return self._result(fabric, initial, step, SolverStatus.DIVERGED)
            if constraint_violation(state) <= self.config.convergence_threshold:
                return self._result(fabric, initial, step, SolverStatus.CONVERGED)
        return self._result(fabric, initial, self.config.max_steps, SolverStatus.MAX_STEPS)

    def _result(self, fabric, initial, steps, status):
        final = fabric.snapshot()
        return SolverResult(final, initial, paradox_index(final), steps, status, check_invariants(final),
                            {"monotonic": None, "decay_rate": None, "convergence_time": steps})
