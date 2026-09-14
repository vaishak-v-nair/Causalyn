"""Finite-dimensional geometry helpers; these are explicit approximations."""
from dataclasses import dataclass
from typing import Any

try:
    import torch
    _TORCH = True
except ImportError:
    torch = None
    _TORCH = False

@dataclass
class MetricTensor:
    """Symmetric positive-definite metric parameter, not an exact manifold metric."""
    value: Any

    @classmethod
    def identity(cls, dimension: int = 3) -> "MetricTensor":
        if _TORCH:
            return cls(torch.eye(dimension, requires_grad=True))
        return cls([[1.0 if i == j else 0.0 for j in range(dimension)]
                    for i in range(dimension)])

    def is_positive_definite(self) -> bool:
        if _TORCH:
            value = self.value if isinstance(self.value, torch.Tensor) else torch.tensor(self.value, dtype=torch.float32)
            return bool(torch.linalg.eigvalsh((value + value.T) / 2).min() > 0)
        return all(self.value[i][i] > 0 for i in range(len(self.value)))

def ricci_approximation(state: Any, metric: Any) -> Any:
    """R_APPROX: diagonal state-energy surrogate, computationally tractable but limited."""
    if _TORCH:
        return torch.diag(state * state) + 0.01 * metric
    return [[(state[i] * state[i] if i == j else 0.0) + 0.01 * metric[i][j]
             for j in range(3)] for i in range(3)]
