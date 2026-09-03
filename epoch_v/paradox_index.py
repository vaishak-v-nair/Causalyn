from typing import Any
from .constraints import constraint_violation

def paradox_index(state: Any, intent: Any = None) -> float:
    """κ is the non-negative sum of executable invariant violations; intent is provenance context."""
    return float(constraint_violation(state))
