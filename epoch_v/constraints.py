from typing import Any, Dict

def _values(state: Any):
    if hasattr(state, "state"):
        state = state.state
    if hasattr(state, "detach"):
        return [float(x) for x in state.detach().tolist()]
    if hasattr(state, "tolist"):
        return [float(x) for x in state.tolist()]
    return [float(x) for x in state]

def constraint_violations(state: Any) -> Dict[str, float]:
    token, session, privilege = _values(state)
    return {
        "revoked_token_active_session": max(0.0, session - token),
        "unauthorized_authenticated_state": max(0.0, session - privilege),
        "out_of_bounds": sum(max(0.0, -x) + max(0.0, x - 1.0) for x in (token, session, privilege)),
    }

def constraint_violation(state: Any) -> float:
    return sum(constraint_violations(state).values())

def check_invariants(state: Any) -> Dict[str, bool]:
    return {name: value <= 1e-6 for name, value in constraint_violations(state).items()}
