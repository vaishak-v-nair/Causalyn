# Epoch-V Agent OS — Documentation Index

This directory is the repository instruction and governance system for the autonomous engineering team building **Causalyn** on **Epoch-V**.

---

## Primary Documents

| Document | Purpose |
|:---|:---|
| [`SPECIFICATION.md`](SPECIFICATION.md) | **Canonical Technical & Architectural Specification** — the single source of truth for Causalyn's 4-layer architecture, technology stack, interfaces, component cards, failure modes, and acceptance criteria. |
| [`AGENTS.md`](AGENTS.md) | **Agent OS Constitution** — load order, mission, priorities, epistemic rules, and protocol matrix for all Epoch-V agents. |
| [`SYSTEM.md`](SYSTEM.md) | **System Constitution** — layers, vocabulary, authority hierarchy, and design constraints. |
| [`HIERARCHY.md`](HIERARCHY.md) | **Agent Hierarchy** — role ownership, authority boundaries, and resolution rules. |
| [`GOVERNANCE.md`](GOVERNANCE.md) | **Consolidated Governance Protocols** — contracts, task protocol, anti-slop, build rules, safety, failure handling, validation, adversary, research, handoff, memory, decisions, and definition of done. |
| [`VPSN_BRIDGE.md`](VPSN_BRIDGE.md) | **Research Bridge** — translating C-VPSN SOURCE concepts into testable engineering experiments. |

## Theory & Source Material

| Document | Purpose |
|:---|:---|
| [`source/VPSN_Deep_Dive_Research.md`](source/VPSN_Deep_Dive_Research.md) | **Canonical SOURCE** — Vaishak Principle theory reference (C-VPSN). Not PROVEN; not rewritable. |
| [`source/SOURCE_STATUS.md`](source/SOURCE_STATUS.md) | **Source Inventory** — what documents exist, which are BLOCKED, and citation rules. |
| [`The_Vaishak_Principle_Illustrated.pdf`](The_Vaishak_Principle_Illustrated.pdf) | **Foundational PDF** — illustrated theory document. |

## Implementation References

| Document | Purpose |
|:---|:---|
| [`specs/prototype-001.md`](specs/prototype-001.md) | Prototype 001 specification and acceptance criteria. |
| [`schemas/`](schemas/) | YAML schemas for agent contracts and enums. |
| [`agents/`](agents/) | Individual agent persona definitions (orchestrator, architect, researcher, builder, adversary, validator, release). |
| [`skills/`](skills/) | Operational skill cards for specific workflows. |

---

## Design Commitments

1. Preserve source terminology and intent (Epoch-V, VPSN, C-VPSN, Intent Vector, Ambient Fabric, Vaishak Operator, Destructive Semantic Interference, CEGAR-CEGIS Loop, Semantic Ricci Flow, AI Harness, AI Orchestration, Shadow Execution, Transactional State / Commit Boundary, Consensus / Verification Gating, EU AI Act Article 10 Audit).
2. Never silently convert SOURCE theory into FACT or PROVEN without deterministic verification.
3. Make agent behavior hard to game: contracts, stages, gates, evidence, fail-closed mutation.

## Reading Order

1. `AGENTS.md` — loadable constitution (every agent)
2. `SYSTEM.md` — layers, vocabulary, authority
3. `SPECIFICATION.md` — canonical technical specification
4. `source/VPSN_Deep_Dive_Research.md` — C-VPSN theory reference
5. `source/SOURCE_STATUS.md` — what documents exist
6. `GOVERNANCE.md` — all protocols (contracts, task lifecycle, safety, validation, etc.)
7. `VPSN_BRIDGE.md` — research bridge

## Current Evidence State

- Causalyn full-stack control plane exists under canonical package `causalyn/` with automated suites under `tests/` and continuum solver under `epoch_v/` (FACT).
- Architecture operationalizes C-VPSN through the 3-stage pipeline: Ambient Fabric ($M(S)$) → Consensus Gate ($\Upsilon$, Independence Principle) → Atomic Commit Boundary (FACT).
- Primary papers and specifications are active and verified (`The_Vaishak_Principle_Illustrated.pdf`, `SPECIFICATION.md`, `source/VPSN_Deep_Dive_Research.md`) (FACT).
- 92 unit, adversarial, and enterprise tests pass with 100% success rate (FACT).
