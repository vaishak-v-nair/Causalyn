# Source Inventory

Status: FACT about this repository after the Prototype 001 implementation pass.

## Present in repository

| ID | Path | Classification | Notes |
|----|------|----------------|-------|
| SRC-VPSN-DEEPDIVE | `docs/source/VPSN_Deep_Dive_Research.md` | SOURCE | Vision / industry-trajectory document. Contains strong scientific and commercial claims. Those claims are SOURCE text, not PROVEN. |
| SRC-SEED-OS | Prior `docs/` skill and agent drafts | SOURCE + IMPLEMENTATION | Informal seed OS. Superseded by this Agent OS where they conflict, except SRC-VPSN-DEEPDIVE. |
| SRC-PROTO-001 | `docs/specs/prototype-001.md` | IMPLEMENTATION (spec + prototype) | First engineering experiment. Does not validate VPSN mathematics. |

## Named in seed OS, not found in repository

| ID | Named source | Status |
|----|--------------|--------|
| SRC-VPSN-PRIMARY | "Supplied VPSN primary paper" | UNKNOWN / BLOCKED for claims that require it |
| SRC-EPOCH-DESIGN | "Supplied Epoch / Agentic AI design document" | UNKNOWN / BLOCKED for claims that require it |

Agents MUST NOT invent the missing papers. If a claim depends on them, mark BLOCKED and request the file.

## How to cite SOURCE

```text
[SOURCE:SRC-VPSN-DEEPDIVE §N] <verbatim or close paraphrase>
[INFERENCE] <engineering reading>
[HYPOTHESIS] <testable claim>
```

## Claims in SRC-VPSN-DEEPDIVE that MUST remain non-PROVEN unless later evidence is recorded

These are SOURCE assertions. They are not FACT about the world and not PROVEN by this repository.

- VPSN "mathematically proves" that building a flawless agent is a localized error.
- Bugs with κ > 0 are physically incapable of existing in the Ambient Fabric.
- CI/CD, QA, and testing become unnecessary.
- Legacy systems can be migrated with zero downtime and zero blast radius via acausal resolution.
- RLHF is functionally useless for execution tasks.
- Autoregressive code generation is obsolete under VPSN.
- The Vaishak Operator annihilates failure before state materializes in computational time.

Engineering work MAY operationalize analogues of these claims. Analogues MUST be labeled IMPLEMENTATION or HYPOTHESIS.
