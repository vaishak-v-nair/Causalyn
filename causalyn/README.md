# Causalyn — Core Package

The `causalyn/` package implements the **Constraint-Gated Shadow Execution** control plane.

## Architecture

```text
causalyn/
├── api/               # FastAPI routes, Pydantic contracts, backend service
├── orchestrator/      # CEGAR-CEGIS state machine + AI orchestrator pipeline
├── shadow/            # Copy-on-write sandbox executor + DB branching
├── verification/      # Deterministic invariant checker (AST, schema, secrets, scope)
├── commit/            # Atomic 2PC commit boundary with SHA-256 OCC
├── translator/        # Natural language → IntentSpecification
├── harness/           # AI harness context (budget, retries, checkpoints)
├── model/             # World state manager + LLM provider protocol
├── storage/           # SQLite WAL / Postgres repository + pipeline store
├── llm/               # Multi-provider LLM adapter (Gemini, Groq, OpenRouter, NVIDIA NIM)
├── failure_pattern/   # Append-only failure pattern dataset
├── services/          # Mission lifecycle service
├── benchmarks/        # M2 synthetic adversarial benchmark suite
├── ci/                # M3 GitHub PR shadow verification
├── staging/           # M4 staging proxy interceptor (K8s, Docker)
├── gating/            # Consensus gate implementation
├── enclave/           # M5 hardware enclave attestation (AMD SEV-SNP / SGX)
├── consensus/         # M5 distributed 4-node Byzantine consensus
├── compliance/        # M5 SOC2 + EU AI Act Article 10 compliance engine
├── config.py          # Runtime settings (env-driven)
├── cli.py             # Enterprise CLI (wrap, intercept, status, benchmark, ci, compliance)
├── main.py            # Demo entry point
└── epoch_v_bridge.py  # Bridge to epoch_v/ research module
```

## Running

```powershell
# Full-stack API + Dashboard
python app.py

# CLI operations
python -m causalyn.cli status
python -m causalyn.cli wrap "echo hello" --target-path "/app"
python -m causalyn.cli benchmark --count 500 --output-dir runtime/benchmarks

# Tests
python -m pytest tests/ -q
```

## Policies

- `policies/invariants.yaml` — protected paths and secret patterns
- `policies/auth.yaml` — authorization policies