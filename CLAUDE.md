# Causalyn Development Guidelines

### Architecture Rules
- Causalyn is a **fail-closed execution hypervisor**. It intercepts all agentic tool usage (shell commands, file edits) via a Copy-on-Write (CoW) shadow directory.
- The host filesystem is immutable until state verification passes: zero file modifications outside `ambient_fabric`.
- Verification must be deterministic (AST + Z3), not LLM-based. No prompt-based checks for safety.
- Toxic actions (e.g., `rm -rf /`, `DROP TABLE`) must trigger instantaneous state annihilation (`annihilate()`) with 0 bytes written to host disk.

### Frontend UI & Aesthetics (skeli-skills compliance)
- The frontend must retain a 3-Zone layout (Swarm RPC Stream, 3D Symplectic Manifold, Ground Truth Vault).
- Absolutely no generic HTML/CSS. Must use the Causalyn glassmorphic design system (`var(--cyan-accent)`, `rgba(15,23,42,0.9)`, etc).
- Use strict micro-animations on interactive elements.

### Telemetry Rules
- Telemetry timestamps require microsecond accuracy via `time.perf_counter_ns()`.
- The WebGL manifold must react to real-time `\kappa` index updates streamed over WebSocket (`ws://127.0.0.1:8000/ws/telemetry`).

### Formal Proof Engine
- Subprocess limits, memory sizes, and thread allocations must be evaluated via the Z3 SMT solver natively in `z3_engine.py`.

*Failure to comply with these rules breaks the core axioms of Semantic Nullification.*
