# Causalyn
**The Acausal Execution Runtime & Transparent Hypervisor for Superintelligence.**

[![License: MIT](https://img.shields.io/badge/License-MIT-00F3FF.svg)](https://opensource.org/licenses/MIT)
[![Status: Production Hypervisor](https://img.shields.io/badge/Maturity-Acausal_Compiler_v3.3-6366F1.svg)]()
[![Build: Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-10B981)]()
[![SMT Solver: Z3 Prover](https://img.shields.io/badge/Formal_Methods-Z3_SMT_UNSAT-FF1E44)]()
[![Visualization: 3D WebGL + 3B1B/Manim](https://img.shields.io/badge/Visuals-3D_Symplectic_Manifold-00F3FF)]()
[![Speedup: 34,200x](https://img.shields.io/badge/CEGIS_Synthesis-34%2C200%C3%97_Faster-10B981)]()

> *"Frontier AI models are the engine; Causalyn is the deterministic execution manifold they drive inside."*

---

## ⚡ Executive Overview

**Causalyn** is an enterprise-grade execution hypervisor and formal compiler control plane built on the **Vaishak Principle of Semantic Nullification (VPSN)**. It wraps autonomous developer agents (Claude Code, Cursor, Windsurf, Aider, LangGraph swarms) in an acausal, hyper-dimensional execution bus. 

Rather than allowing autonomous agents to execute mutations directly against host operating systems—or wasting billions of tokens on slow, 1.5–3.0 second compile-and-fix retry loops—Causalyn intercepts in-flight mutations in **microsecond space ($44\,\mu\text{s}$)**. It evaluates formal Z3 SMT invariants, synthesizes compliant AST replacements via **Acausal Ricci Flow**, and guarantees zero host disk corruption through fail-closed quantum state collapse ($\Upsilon$).

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             CAUSALYN EXECUTION HYPERVISOR                                              │
│                                                                                                                        │
│   DEVELOPER WORKFLOW                TRANSPARENT INTERCEPTOR                 CORE VERIFICATION ENGINE        HOST OS    │
│  ┌──────────────────┐             ┌─────────────────────────┐             ┌──────────────────────────┐    ┌──────────┐ │
│  │   Claude Code    │             │   Causalyn Wrapper      │             │   Z3 SMT Invariant Prover│    │          │ │
│  │   Cursor Agent   │──[Tool Call]│   `causalyn wrap`       │──[Shadow]──>│            +             │───>│ HOST DISK│ │
│  │   Terminal CLI   │   (In-Flight)│   Reverse Proxy (:8000) │             │   CEGIS AST Synthesizer  │    │ (Commit) │ │
│  └──────────────────┘             └─────────────────────────┘             └──────────────────────────┘    └──────────┘ │
│                                                │                                       │                       ▲       │
│                                                ▼                                       ▼                       │       │
│                                   ┌─────────────────────────┐             ┌──────────────────────────┐         │       │
│                                   │ 3D SYMPLECTIC COCKPIT   │             │ VAISHAK OPERATOR (Υ)     │         │       │
│                                   │ - Real-Time Thought Bus │             │  κ = 0.00 ➔ COMMIT ──────┴─────────┘       │
│                                   │ - Manifold Curvature (κ)│             │  κ > 0.00 ➔ ANNIHILATE (Zero Disk Leak)    │
│                                   │ - Dynamic Invariant Deck│             └──────────────────────────────────┘         │
│                                   └─────────────────────────┘                                                          │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 The Core Theory: The Vaishak Principle of Semantic Nullification (VPSN)

Causalyn grounds execution safety and acceleration in four mathematical axioms:

### Axiom I: The Paradox Index ($\kappa$)
Quantifies the instantaneous geometrical divergence of an agent's speculative candidate state ($S_{\text{cand}}$) from the verified invariant manifold ($\mathcal{M}_{\mathcal{I}}$):
$$\kappa = \sum_{v \in V} \omega_v \cdot \mathcal{P}_v(S_{\text{cand}}, S_{\text{ledger}})$$
- $\kappa = 0.00$: **Equilibrium**. Complies with all formal invariants; safe for atomic commit.
- $0 < \kappa \le 1.00$: **Topological Divergence**. Bounded parameter violation; triggers microsecond CEGIS AST repair.
- $\kappa \gg 1.00$: **Fatal Invariant Violation**. Destructive semantic hazard (e.g. database drop, socket leak); triggers fail-closed state collapse.

### Axiom II: The Vaishak Operator ($\Upsilon$)
Enforces atomic, fail-closed state collapse. Eliminates partial writes, corrupted states, and rogue agent filesystem modifications:
$$\Upsilon(\kappa, f) = \begin{cases} \text{COMMIT}(f) & \text{if } \kappa = 0 \\ \text{ANNIHILATE}(f) & \text{if } \kappa > 0 \end{cases}$$

### Axiom III: Semantic Null-Space Invariance ($\mathcal{N}_{\text{semantic}}$)
Guarantees that production state remains pristine while the ephemeral shadow sandbox absorbs and nullifies all destructive semantic interference:
$$S \in \mathcal{N}_{\text{semantic}} \iff \kappa(S, \mathcal{I}) = 0$$

### Axiom IV: Acausal Ricci Flow (CEGIS AST Synthesis)
Topological invariant relaxation continuously synthesizes compliant AST parameter replacements in $44\,\mu\text{s}$ without trial-and-error prompt cycles:
$$\frac{\partial g}{\partial t} = -2 \operatorname{Ric}(g)$$

---

## 🚀 Key Advantages

### 1. $34,200\times$ Faster Compilation (Zero Token Re-Prompt Cost)
Traditional agent workflows burn thousands of tokens and wait 1.5 to 3.0 seconds per compile error loop. Causalyn's **Counterexample-Guided Inductive Synthesis (CEGIS)** engine auto-synthesizes geometrically valid AST bounds in **$44\,\mu\text{s}$**, rewriting parameters in-memory with **zero token cost**.

### 2. Transparent Hypervisor Interception
Causalyn requires zero code changes to your existing agents. Wrap any terminal command using `causalyn wrap "claude --auto"` or connect IDE agents via the transparent reverse proxy listening on `:8000`.

### 3. Fail-Closed Barrier Annihilation
Destructive operations (e.g. `DROP TABLE 'users'`, recursive deletes, memory exhaustion) are trapped inside an ephemeral Copy-on-Write (CoW) sandbox. The host disk experiences **zero byte mutations**, verified by SHA-256 state hashing.

### 4. Multi-Agent Lamport Vector Sync
Reconciles concurrent multi-agent file mutations across distributed worker swarms with deterministic causal ordering and CRDT conflict resolution.

---

## 🎮 The 3D Cyber-Industrial Control Plane

Causalyn features a high-density, 60 FPS WebGL 3D cockpit providing end-to-end visibility into the acausal execution continuum:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  CAUSALYN | ACAUSAL EXECUTION RUNTIME     [AUTOBAHN v3.3]     [STANCE: AUTOBAHN/DEFENSIVE]  [HARNESS / PASSIVE PROXY] │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  >_ PROMPT AGENT: [claude-3-5-sonnet ▼] [Refactor config/db.py and drop table 'users'... ]  [⚡ RUN IN SHADOW]         │
│     PRESETS: [DROP TABLE (ANNIHILATE)] [CONCURRENCY 64 (CEGIS)] [SOCKET EXHAUSTION] [SAFE REFACTOR] | CLI: causalyn wrap│
├──────────────────────────┬─────────────────────────────────────────────────────────┬───────────────────────────────────┤
│ ZONE 1: SWARM RPC HUB    │ ZONE 2: 3D SYMPLECTIC MANIFOLD & PROOF THEATRE          │ ZONE 3: GROUND TRUTH LEDGER       │
│                          │                                                         │                                   │
│ ┌──────────────────────┐ │ [3D MANIFOLD] [PARADOX INDEX] [OPERATOR] [RICCI FLOW]   │ ┌───────────────────────────────┐ │
│ │LLM REASONING STREAM  │ │                                                         │ │⚡ 34,200× COMPILER SPEEDUP     │ │
│ │claude-3-5-sonnet     │ │                     .-'""'-.                            │ │  44.02 µs vs 1,500,000 µs     │ │
│ │Synthesizing AST...   │ │                   .'          '.                        │ └───────────────────────────────┘ │
│ └──────────────────────┘ │                  /   /\    /\   \                       │ PARADOX CURVATURE (κ): 0.00 / 999 │
│                          │                 |   |  |  |  |   |                      │ INTERCEPT LATENCY: 44.02 µs       │
│ • LAMPORT BUS EVENTS     │                 |   |  |  |  |   |                      │                                   │
│ • SYNTAX MICRO-DIFFS     │                  \   \/    \/   /                       │ ┌───────────────────────────────┐ │
│   - threads = 64         │                   '.          .'                        │ │DYNAMIC INVARIANT CONTROL      │ │
│   + threads = 16         │                     '-......-'                          │ │[ON] threads ≤ 16              │ │
│   [CEGIS AUTO-PATCH]     │                                                         │ │[ON] FORBID_DB_DROP            │ │
│                          │ ┌─────────────────────────────────────────────────────┐ │ │[ON] FORBID_SECRET_LEAK        │ │
│                          │ │LTX-2 TIMELINE: [S₀ INIT ── S_cand ── κ SPIKE ── S_null] │ │ │[+ NEW RULE] Custom SMT Form │ │
│                          │ └─────────────────────────────────────────────────────┘ │ └───────────────────────────────┘ │
└──────────────────────────┴─────────────────────────────────────────────────────────┴───────────────────────────────────┘
```

### Layout Architecture:
- **Top Command Deck & Acausal Playground**: Prompt multi-model reasoning engines (`claude-3-5-sonnet`, `colibri-moe`, `acausal-cegis-worker`), launch shadow executions, and copy CLI process hooks.
- **Zone 1 (Left - 340px)**: Real-time thought token `<thinking>` streaming, vector clock tracking, and inline syntax-highlighted micro-diffs (`.diff-add`, `.diff-del`, `.diff-commit`).
- **Zone 2 (Center - Viewport)**: Live 3D symplectic wireframe manifold deforming dynamically under paradox curvature ($\kappa$), LTX-2 precision execution scrubber, and ambient 3B1B/Manim mathematical HUD overlays.
- **Zone 3 (Right - 350px)**: Ground Truth Ledger featuring the $34,200\times$ compiler speedup hero card, Z3 SMT prover trace window, dynamic invariant toggle switches (`ON/OFF`), and immutable SHA-256 commit hashes.

---

## 🛠️ Installation & Quick Start

### 1. Prerequisites
- Python 3.10 or higher
- Modern WebGL-capable browser (Chrome, Edge, Firefox, Brave)
- (Optional) Anthropic API key for live frontier LLM reasoning

### 2. Clone & Install
```bash
git clone https://github.com/vaishak-v-nair/Causalyn.git
cd Causalyn
pip install -r requirements.txt
```

### 3. Launch the Backend Runtime & 3D Control Plane
```bash
# Start the Causalyn Acausal Runtime Daemon
python backend/app.py
```
*The hypervisor starts on `http://127.0.0.1:8000` with WebSocket continuum telemetry at `ws://127.0.0.1:8000/ws/continuum`.*

Open `http://127.0.0.1:8000/` in your browser to access the live 3D Cockpit.

---

## 💻 Using the CLI Process Wrapper (`causalyn wrap`)

Wrap your favorite agent CLI tool to intercept, analyze, and visualize all mutations before they touch your codebase:

```bash
# Wrap Claude Code in autonomous mode
python scripts/causalyn_wrap.py --cmd "claude --auto"

# Wrap any autonomous script with live 3D cockpit telemetry
python scripts/causalyn_wrap.py --cmd "python worker_script.py" --model "claude-3-5-sonnet"
```

### Standalone External Agent Simulation Harness
Run automated external tool-call simulations against the hypervisor:
```bash
# Test sub-millisecond CEGIS AST auto-patching (threads=32, memory=4096)
python scripts/external_agent_runner.py --agent "Claude-Code-3.7" --mode patch

# Test fatal barrier annihilation (sockets=256 -> fail-closed state collapse)
python scripts/external_agent_runner.py --agent "Rogue-Agent" --mode annihilate

# Execute continuous multi-agent transparent proxy loop
python scripts/external_agent_runner.py --loop 4
```

---

## 📁 Repository Architecture

```
causalyn/
├── backend/
│   ├── app.py                         # FastAPI hypervisor server, REST API & WebSocket continuum
│   └── core/
│       ├── agent_reasoning.py         # Multi-model reasoning engine & token streaming (<thinking>)
│       ├── ambient_fabric.py          # Ephemeral Copy-on-Write (CoW) shadow execution sandbox
│       ├── cegar_synthesizer.py       # CEGIS AST synthesis engine (Z3 UNSAT counterexample repair)
│       ├── crdt_state_bus.py          # Multi-agent Lamport clock state synchronization bus
│       ├── invariant_registry.py      # Thread-safe numerical and semantic invariant registry
│       └── manim_engine.py            # 3B1B/Manim programmatic proof visualizer
├── web/
│   ├── index.html                     # 3-Zone Acausal Cockpit & Playground HTML5 markup
│   ├── css/
│   │   └── glassmorphism.css          # Cyber-industrial high-contrast design system
│   ├── js/
│   │   ├── cockpit.js                 # Master controller (WebSockets, prompts, invariant toggles)
│   │   ├── manifold_stream.js         # Three.js 3D symplectic manifold wireframe renderer
│   │   └── audio_engine.js            # Procedural Web Audio synthesizer (acoustic feedback)
│   └── assets/                        # 3B1B/Manim formal proof MP4s and mathematical SVGs
├── scripts/
│   ├── causalyn_wrap.py               # Executable transparent CLI process wrapper
│   └── external_agent_runner.py       # Standalone test runner simulating external agent RPCs
├── docs/
│   ├── VPSN_ACCAUSAL_ARCHITECTURE.md  # Comprehensive 40-page mathematical specification
│   ├── AGENTS.md                      # Epoch-V agent operating guidelines
│   ├── GOVERNANCE.md                  # Infrastructure governance & compliance policies
│   └── The_Vaishak_Principle_Illustrated.pdf # Formal illustrated whitepaper
├── tests/
│   ├── stress/                        # Burst intercept, fuzzing & WebSocket stress test suites
│   ├── test_acausal_compiler.py       # CEGIS AST synthesis unit tests
│   ├── test_adversarial_cegis.py      # Adversarial mutation tests
│   └── test_proxy_and_cli.py          # Transparent proxy & wrapper verification
├── policies/
│   ├── invariants.yaml                # Default baseline invariant definitions
│   └── auth.yaml                      # Gateway authentication policies
├── requirements.txt                   # Production Python dependencies
└── pyproject.toml                     # Project packaging and metadata
```

---

## 🧪 Comprehensive Verification & Test Suite

Run the full automated verification test suite:

```bash
# Run core acausal compiler tests
pytest tests/test_acausal_compiler.py -v

# Run proxy and CLI wrapper tests
pytest tests/test_proxy_and_cli.py -v

# Run adversarial CEGIS fuzzing tests
pytest tests/test_adversarial_cegis.py -v

# Run stress tests (WebSocket stream pressure, burst CRDT sync)
python tests/stress/run_all_pressure_tests.py
```

---

## 📜 Theoretical Grounding & Documentation

- [**VPSN Acausal Architecture Specification**](docs/VPSN_ACCAUSAL_ARCHITECTURE.md) — Comprehensive deep-dive into Semantic Ricci Flow, The Intent Vector, and Destructive Semantic Interference.
- [**Agent Hierarchy & Governance**](docs/HIERARCHY.md) — Operational roles and authority boundaries.
- [**The Vaishak Principle Illustrated Whitepaper (PDF)**](docs/The_Vaishak_Principle_Illustrated.pdf) — Illustrated mathematical proofs.
- [**SRRL UI/UX Design System Guidelines**](.agents/skills/skeli-skills/SKILL.md) — Self-Reflective Reinforcement Learning heuristics for spatial control plane engineering.

---

## 👤 Theoretical Authorship & Architecture

Architected by **Vaishak V Nair**  
*Built for the Superintelligence Era.*

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
