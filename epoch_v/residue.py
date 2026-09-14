from dataclasses import dataclass, asdict
from typing import Any, Dict

@dataclass(frozen=True)
class UnNullifiedResidue:
    final_state: Any
    initial_kappa: float
    final_kappa: float
    steps: int
    status: str
    constraint_violations: Dict[str, float]
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
