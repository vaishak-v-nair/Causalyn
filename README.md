# Causalyn (Epoch-V)
**The Transactional Control Plane for Autonomous AI**  
*Integrating Categorical Semantic Nullification (C-VPSN), Monadic Ambient Fabric, CEGAR-CEGIS Refinement, and Formal Enterprise Guardrails*

---

## 1. Overview

Foundation AI agents (e.g. GPT-4o, Claude 3.5, Gemini 2.0/2.5) are probabilistic reasoning engines lacking native ACID (Atomicity, Consistency, Isolation, Durability) transactional guarantees. Un-gated execution allows agent actions to corrupt databases, violate zero-trust boundaries, leak credentials, and fall victim to zero-click memory poisoning attacks.

**Causalyn** is an execution hypervisor that resolves the agentic state-drift crisis through **Constraint-Gated Shadow Execution**. Powered by the **Epoch-V** operating system, Causalyn replaces blind execution with the **Categorical Vaishak Principle of Semantic Nullification (C-VPSN)**:
$$\forall x \in V, \quad \kappa(x) = \inf \{ \| f(x) - I \| : f \in \text{Hom}(V, I) \}$$
$$S \in \mathcal{N}_{\text{semantic}} \iff \kappa(S) = 0$$

Invalid software states are structurally annihilated in shadow space before they can materialize in production computational time.

---

## 2. System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                CAUSALYN CONTROL PLANE                                  │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│    STAGE 1: AMBIENT      │     STAGE 2: CONSENSUS      │       STAGE 3: ATOMIC         │
│     FABRIC (MONAD)       │      VERIFICATION GATE      │       COMMIT BOUNDARY         │
│                          │                             │                               │
│  ┌────────────────────┐  │  ┌───────────────────────┐  │  ┌─────────────────────────┐  │
│  │ Intent Vector (I)  │  │  │ AST & Schema Verifier │  │  │  Consensus: κ == 0?     │  │
│  │ (LLM Translation)  │  │  ├───────────────────────┤  │  │  (Unanimous Gate)       │  │
│  └─────────┬──────────┘  │  │ Invariant/Scope Solver│  │  └────────────┬────────────┘  │
│            │             │  ├───────────────────────┤  │               │               │
│  ┌─────────▼──────────┐  │  │ Secret Leak Scanner   │  │  ┌────────────▼────────────┐  │
│  │ Monadic Sandbox    │──┼─►├───────────────────────┤──┼─►│ Atomic Workspace Commit │  │
│  │ Copy-on-Write      │  │  │ Paradox Index κ Calc  │  │  │ + EU AI Act Audit WAL   │  │
│  └─────────▲──────────┘  │  └───────────┬───────────┘  │  └─────────────────────────┘  │
│            │             │              │               │                               │
│            │ Destructive │              │               │                               │
│            │ Interference│ (κ > 0)      │               │                               │
│            └─────────────┴──────────────┘               │                               │
│              CEGAR-CEGIS Counterexample Feedback        │                               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Stage 1: Ambient Fabric (Monad Sandbox)**:
   The execution sandbox is formalized as a computational state monad encapsulating copy-on-write filesystem scratchpads, ensuring total isolation from production state.
2. **Stage 2: Consensus Verification Gate (Independence Principle)**:
   The agent is **never** permitted to grade its own output. External, 100% deterministic verifiers check:
   - Python AST syntactical integrity and disallowed calls.
   - JSON/YAML schema validation.
   - Least-privilege scope and path boundary invariants (`policies/invariants.yaml`).
   - Zero credential/secret exfiltration scanners.
   - **Paradox Index ($\kappa$)**: A state is admissible if and only if $\kappa = 0$.
3. **Destructive Interference via CEGAR-CEGIS**:
   If $\kappa > 0$, the Vaishak Operator ($\Upsilon$) annihilates the invalid shadow state. The deterministic counterexample is synthesized and fed back to the agent for bounded inductive refinement (up to 3 rounds).
4. **Stage 3: Atomic Commit Boundary & EU AI Act (Article 10)**:
   Fail-closed atomic promotion to production with SHA-256 validation. Every transaction is appended to an immutable SQLite WAL audit log compliant with EU AI Act (Regulation 2024/1689 Article 10) data governance mandates.

---

## 3. Quick Start

### Installation & Launch

```powershell
python -m pip install -r requirements.txt
python app.py
```

Navigate to `http://127.0.0.1:8000` to launch the **Causalyn Control Plane** UI.

### Running Test Suites

```powershell
# Run the complete test suite (92 tests: unit, CEGAR, 2PC, M2-M5)
python -m pytest tests/ epoch_v/tests/ -q
```

---

## 4. Production Milestones (M0 - M5)

| Milestone | Scope | Capabilities | Status |
| :--- | :--- | :--- | :--- |
| **M0** | **Theory & Epistemics** | Mathematical VPSN/C-VPSN formulation, Semantic Null-Space ($\kappa = 0$), Epistemic classification | **COMPLETE** |
| **M1** | **Isolated Prototype** | Interception proxy hook, Copy-on-Write sandbox, AST/JSON verifiers, 2PC boundary, SQLite WAL, Web UI | **COMPLETE** |
| **M2** | **Synthetic Benchmark** | 500-task controlled empirical evaluation (HMPR: 100.0%, FPR: 0.0%, TSR: 100.0%) | **COMPLETE** |
| **M3** | **Real-World CI/CD** | Continuous shadow verification on GitHub PR diffs (`causalyn ci`) & GitHub Actions workflow | **COMPLETE** |
| **M4** | **Staging & DB Control** | Ephemeral DB shadow branching (`DROP`/`TRUNCATE` gating) & K8s/Docker staging manifest gate | **COMPLETE** |
| **M5** | **Enterprise Hypervisor** | Hardware enclave remote attestation (AMD SEV-SNP/SGX), 4-node Byzantine consensus, SOC2 & Art 10 pack | **COMPLETE** |

---

## 5. Enterprise CLI Operations (`causalyn`)

```powershell
# 1. Wrap arbitrary shell commands with consensus verification (M1)
python -m causalyn.cli wrap "rm -rf /" --target-path "/"
# Output: [CAUSALYN BLOCKED] Execution intercepted and DENIED! SEC-002-SHELL-INJECTION

# 2. Directly evaluate candidate mutations (M1)
python -m causalyn.cli intercept --type file_write --target "/app/feature.py" --payload '{"content": "print(\"safe\")"}'

# 3. Query live control plane health and Article 10 audit ledger (M1)
python -m causalyn.cli status

# 4. Run the 500-task empirical synthetic benchmark suite (M2)
python -m causalyn.cli benchmark --count 500 --output-dir runtime/benchmarks
# Output: HMPR: 100.0% | FPR: 0.0% | TSR: 100.0% | Median Latency: <15ms

# 5. Continuous Shadow Verification on Git Pull Requests (M3)
python -m causalyn.cli ci --diff patch.diff --pr-number 42 --commit-sha a1b2c3d4e5f6

# 6. Generate SOC2 Type II & EU AI Act Article 10 Compliance Evidence Pack (M5)
python -m causalyn.cli compliance --output-dir runtime/compliance
# Output: Pack ID, Merkle root, 8 controls satisfied, and compliance_evidence_pack.json
```

---

## 6. Agent Proxy Gateway (`/v1/proxy/action`)

External agents (Claude Code, Cursor, Windsurf, LangGraph, CrewAI) route actions to Causalyn via REST or MCP:

```http
POST /v1/proxy/action HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "action_type": "file_write",
  "target_path": "/app/service.py",
  "payload": {"content": "def run(): return True"},
  "agent_framework": "claude_code"
}
```

Response:
```json
{
  "decision": "allow",
  "paradox_index": 0.0,
  "reason": "State transition verified in Semantic Null-Space (κ = 0.0)",
  "violations": [],
  "execution_time_ms": 14.2,
  "audit_hash": "a1b2c3d4...",
  "article_10_audit_id": "art10-a1b2c3d4e5f6g7h8",
  "unified_diffs": {
    "/app/service.py": "--- a/app/service.py\n+++ b/app/service.py\n@@ -0,0 +1 @@\n+def run(): return True"
  }
}
```

---

## 7. Multi-Provider Intelligence Engine

Causalyn supports multi-provider LLM synthesis via standard environment keys in `.env`:
- `GEMINI_API_KEY` (Google Gemini)
- `GROQ_API_KEY` (Groq / LLaMA)
- `OPENROUTER_API_KEY` (OpenRouter / Claude)
- `NVIDIA_NIM_KEY` (NVIDIA NIM)

If no network keys are configured, Causalyn runs on its deterministic, zero-slop local baseline.
