# Causalyn
**The Acausal Execution Runtime for Superintelligence.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: M1 Prototype](https://img.shields.io/badge/Maturity-M1_Prototype-blue.svg)]()
[![Build: Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)]()

Frontier AI models are the engine; Causalyn is the physics simulation they drive inside. 

Built on the **Vaishak Principle of Semantic Nullification (VPSN)**, Causalyn is a deterministic execution control plane that wraps autonomous agents (Claude Code, Cursor, Windsurf) in a hyper-dimensional state bus. It mathematically eliminates trial-and-error latency, auto-corrects architectural paradoxes before they compile, and forces perfect multi-agent synchronization.

Causalyn doesn't just make AI safe. It makes it flawless.

## ⚡ The Acausal Advantage

1. **Zero-Latency Compilation:** Stop burning tokens on compiler errors. Causalyn's CEGIS-driven $\kappa$-Engine uses formal Z3 theorem proving to mathematically intercept and correct structural paradoxes before code touches the host disk.
2. **The Ambient Fabric:** A sub-millisecond, copy-on-write execution sandbox. Agents mutate a localized monad; the real filesystem is only atomically updated if the Paradox Index ($\kappa = 0$).
3. **Multi-Agent State Sync:** Run swarms of agents without state degradation. Causalyn detects geometric conflicts between concurrent AI workers and structurally blocks destructive interference.

## 🏗️ Architecture

Causalyn operates as a 4-Layer Interception Stack:
* **Layer 1: The Gateway Hook** - Transparently intercepts JSON-RPC tool calls from any agent framework.
* **Layer 2: The Ambient Fabric** - Ephemeral workspace cloning (Local memory or remote microVMs).
* **Layer 3: The VPSN Consensus Engine** - Python AST parsing, Z3 constraint satisfaction, and schema verification compute the exact curvature of the failure ($\kappa$).
* **Layer 4: The Vaishak Operator** - An atomic, fail-closed commit boundary. If $\kappa > 0$, the state is annihilated.

## 🚀 Quick Start (Local M1 Prototype)

### 1. Installation
Clone the repository and install the formal verification dependencies:
```bash
git clone https://github.com/vaishak-v-nair/Causalyn.git
cd Causalyn
pip install -r requirements.txt
```
(Requires z3-solver, fastapi, uvicorn, and anthropic)

### 2. Boot the Continuum UI
Launch the WebGL-powered 3D state visualizer to watch Destructive Semantic Interference in real-time.
```bash
# Start the WebSocket backend
uvicorn app:api --reload
```
Open `web/index.html` in your browser.

### 3. Run the Interception Harness
Test the exact millisecond Causalyn intercepts an agent hallucination.
```bash
export ANTHROPIC_API_KEY="your-api-key"
python test_interception.py
```
Watch the terminal confirm zero bytes written to the host, while the 3D WebGL dashboard visualizes the state annihilation.

## 🧠 Core Theory
For a deep dive into the mathematics driving this runtime (Semantic Ricci Flow, The Intent Vector, and Destructive Semantic Interference), read the architectural specification: [docs/VPSN_ACCAUSAL_ARCHITECTURE.md](docs/VPSN_ACCAUSAL_ARCHITECTURE.md).

Architected by Vaishak V Nair
