"""Reproducible experiment runner and append-only JSON logging."""
from dataclasses import asdict
from pathlib import Path
import json, time, uuid
from .config import RuntimeConfig
from .ambient_fabric import AuthenticationManifold
from .intent_translator import IntentTranslator
from .ricci_flow_solver import RicciFlowSolver

def run_experiment(log_path: str | None = None) -> list[dict]:
    config = RuntimeConfig()
    translator = IntentTranslator()
    intent = translator.encode("authenticated session requires a valid token and authorized privilege")
    cases = {"valid": (1, 1, 1), "causality_tear": (0, 1, 1), "unauthorized": (1, 1, 0)}
    records = []
    for name, state in cases.items():
        start = time.perf_counter()
        result = RicciFlowSolver(config).solve(AuthenticationManifold(state, config.rigidity_strength), intent)
        record = {"experiment_id": str(uuid.uuid4()), "code_version": "epoch-v-runtime-1",
                  "configuration": asdict(config), "intent": intent.provenance,
                  "initial_state": state, "initial_kappa": result.initial_kappa,
                  "solver": "Adam-like projected gradient", "learning_rate": config.learning_rate,
                  "steps": result.steps, "final_kappa": result.final_kappa,
                  "constraint_results": result.constraint_results, "runtime": time.perf_counter()-start,
                  "status": result.status.value, "limitations": result.limitations}
        records.append(record)
    if log_path:
        with Path(log_path).open("a", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record) + "\n")
    return records

if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2))
