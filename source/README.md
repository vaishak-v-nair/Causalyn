# Epoch-V Prototype 001: Constraint-Gated Shadow Execution

This is an implementation of the Epoch-V agent operating system's Prototype 001, which implements constraint-gated shadow execution to reduce harmful state mutations.

## Components

- `source/harness/context.py` - AI Harness (context, tools, memory, budgets, retries, checkpoints)
- `source/translator/intent_translator.py` - Intent Translator (NL → Intent Specification)
- `source/model/world_state.py` - World/State Model (snapshotable state with filesystem)
- `source/shadow/executor.py` - Shadow Execution (isolated tmpfs filesystem)
- `source/verification/invariant_checker.py` - Verification Engine (multi-verifier consensus gating)
- `source/commit/boundary.py` - Commit Boundary (authorization, persistence, audit log)
- `source/failure_pattern/dataset.py` - Failure-Pattern Dataset (append-only logs)
- `source/orchestrator/orchestrator.py` - AI Orchestrator (pipeline: translate → shadow → verify → commit)
- `source/main.py` - Demonstration script

## Policies

- `policies/invariants.yaml` - protected paths and secret patterns
- `policies/auth.yaml` - authorization policies

## Running the Tool

From the repository root:

```bash
python -m source.main
```

This will run a demonstration with several test intents and show the pipeline stages, verification decisions, commit decisions, and resulting state.

## Test Suite

A basic test for the harness context is available:

```bash
python -m unittest tests.test_harness_context
```

## Next Steps for Production Readiness

See the tasks listed in the plan file (`C:\Users\vaish\.claude\plans\you-are-a-top-harmonic-conway.md`) and the tasks JSONL artifact in `~/.gstack/projects/causalyn/tasks-eng-review-*.jsonl`.

Implement the T1-T10 tasks in order to harden the system for production use.