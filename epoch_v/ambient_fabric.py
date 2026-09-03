from dataclasses import dataclass
from typing import Any, Sequence
from .geometry import MetricTensor

try:
    import torch
    import torch.nn as nn
    _TORCH = True
except ImportError:
    torch = None
    nn = object
    _TORCH = False

@dataclass(frozen=True)
class AuthenticationState:
    token_valid: float
    session_active: float
    privilege_authorized: float

    def as_sequence(self) -> tuple:
        return (float(self.token_valid), float(self.session_active), float(self.privilege_authorized))

class AuthenticationManifold(nn.Module if _TORCH else object):
    """Finite-dimensional Ambient Fabric shadow state; coordinates are not a real manifold."""
    def __init__(self, initial_state: Sequence[float] = (1.0, 1.0, 1.0), rigidity_strength: float = 2.0):
        if len(initial_state) != 3:
            raise ValueError("authentication state requires three coordinates")
        if _TORCH:
            super().__init__()
            self.state = nn.Parameter(torch.tensor(initial_state, dtype=torch.float32))
            self.metric = nn.Parameter(torch.eye(3))
        else:
            self.state = [float(x) for x in initial_state]
            self.metric = MetricTensor.identity().value
        self.rigidity_strength = float(rigidity_strength)

    def snapshot(self) -> tuple:
        return tuple(float(x) for x in (self.state.detach().tolist() if _TORCH else self.state))
