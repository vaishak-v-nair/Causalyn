# Causalyn

**The AI Execution Checkpoint & Cross-Vendor Verification Harness**

Causalyn is an execution harness for autonomous coding agents. It provides a deterministic `CheckpointEngine` to wrap AI agent loops, capture execution state, run causal bisection on failures, and verify fixes using a cross-vendor model consensus gate.

## Core Capabilities

- **State Checkpointing**: Roll back and reconstruct git states effortlessly when an agent failure occurs.
- **Causal Bisection**: Automatically identify the exact turn/step where a bug was introduced.
- **Cross-Vendor Verification Gate**: Employs an independent, secondary model (e.g., Llama 3.1 70B via NIM, or Groq) to review agent patches and confirm they fix the root cause, rather than just suppressing symptoms.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/vaishak-v-nair/Causalyn.git
cd Causalyn

# Install the framework
pip install -e .[dev]

# Run the test suite
pytest tests/ -v
```

## Repository Structure

- `causalyn/`: Core framework (CheckpointEngine, Bisection, Verifier, MCP hooks).
- `sample_repo/`: Demo repository showcasing integration.
- `tests/`: Pytest suite covering all framework features.

## License

MIT License
