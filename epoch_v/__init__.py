"""Epoch-V numerical runtime (experimental finite-dimensional approximation)."""

from .config import RuntimeConfig
from .intent_translator import IntentMatrix, IntentTranslator
from .ambient_fabric import AuthenticationManifold, AuthenticationState
from .constraints import check_invariants, constraint_violation
from .paradox_index import paradox_index
from .ricci_flow_solver import RicciFlowSolver, SolverResult, SolverStatus

__all__ = [
    "RuntimeConfig", "IntentMatrix", "IntentTranslator",
    "AuthenticationManifold", "AuthenticationState", "check_invariants",
    "constraint_violation", "paradox_index", "RicciFlowSolver", "SolverResult",
    "SolverStatus",
]
