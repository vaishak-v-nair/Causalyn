from dataclasses import dataclass

@dataclass(frozen=True)
class RuntimeConfig:
    dimension: int = 3
    learning_rate: float = 0.08
    max_steps: int = 100
    convergence_threshold: float = 1e-4
    stability_threshold: float = 1e6
    rigidity_strength: float = 2.0
    seed: int = 0

    def __post_init__(self) -> None:
        if self.dimension != 3:
            raise ValueError("the authentication prototype has exactly three coordinates")
        if self.learning_rate <= 0 or self.max_steps < 1:
            raise ValueError("learning_rate must be positive and max_steps must be positive")
        if self.rigidity_strength < 0:
            raise ValueError("rigidity_strength cannot be negative")
