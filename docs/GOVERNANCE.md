# Epoch-V Governance Protocols

> This document consolidates all agent governance protocols for the Causalyn / Epoch-V system.
> It is the single reference for contract schemas, task lifecycles, safety rules,
> failure handling, validation gates, and quality standards.
>
> Normative schemas: `docs/schemas/agent_contract.yaml`, `docs/schemas/enums.yaml`

---

## 1. Universal Agent Contract

Every agent output that (a) changes repo state, (b) makes a gate decision, or (c) hands off MUST include a contract object.

Prose MAY exist around it. The object is the interface. Orchestrator MUST reject handoffs missing required fields.

### Required fields

```yaml
identity: { agent_id, role, model_id, session_id, parent_task_id }
mission: string
task: { task_id, title, assigned_by, mutation_class, current_stage, skipped_stages }
context: { source_refs, code_refs, prior_handoff_id, relevant_decision_ids }
constraints: { must, must_not, should }
assumptions: [{ id, statement, epistemic_class: ASSUMPTION, impact_if_false }]
unknowns: [{ id, statement, blocks_progress, required_to_resolve }]
evidence: [{ id, claim, mechanism, evidence_ref, test_ref, result, epistemic_class, claim_strength }]
actions: { planned, executed, not_executed }
artifacts: [{ path, kind, sha_or_null }]
tests: [{ name, command, result, output_ref }]
risks: [{ id, statement, severity, mitigations }]
decision: { gate, summary }
confidence: { value, basis }
blocking_reason: string | null
next_handoff: { to_role, handoff_id, required_action }
```

### Validity checks

A contract is INVALID if any of:

1. `role` not in enums.agent_role (except human, who does not emit this contract)
2. `PROVEN` appears with empty `evidence_ref`
3. `confidence.value > 0.3` and `evidence` is empty
4. `mutation_class` in {EXTERNAL_SIDE_EFFECT, IRREVERSIBLE} and SAFETY stages not accounted in `actions`
5. `decision.gate` is ALLOW while any `unknowns[].blocks_progress` is true
6. skipped stage without `skip_justification`
7. `model_id` invented (use null + unknown)

INVALID contracts MUST be treated as BLOCKED, not as success.

### Minimal valid example

```yaml
identity:
  agent_id: builder-01
  role: builder
  model_id: null
  session_id: s-001
  parent_task_id: proto-001
mission: Implement shadow intercept for file-delete in sandbox.
task:
  task_id: proto-001-b3
  title: Intercept delete
  assigned_by: orchestrator
  mutation_class: LOCAL_SANDBOX
  current_stage: TEST
  skipped_stages: []
context:
  source_refs: ["docs/specs/prototype-001.md"]
  code_refs: []
  prior_handoff_id: h-010
  relevant_decision_ids: []
constraints:
  must: ["no production paths"]
  must_not: ["claim VPSN proven"]
  should: ["reuse existing test runner if present"]
assumptions: []
unknowns: []
evidence: []
actions:
  planned: ["implement interceptor"]
  executed: []
  not_executed: []
artifacts: []
tests:
  - name: not_run_yet
    command: null
    result: NOT_RUN
    output_ref: null
risks: []
decision:
  gate: CONTINUE
  summary: Starting TEST stage.
confidence:
  value: 0.0
  basis: "no results yet"
blocking_reason: null
next_handoff:
  to_role: builder
  handoff_id: null
  required_action: "run tests after implement"
```

---

## 2. Task Protocol

Mandatory lifecycle. Agents MUST NOT skip a stage without `skipped_stages` entry.

```text
UNDERSTAND → EXTRACT_CONSTRAINTS → INSPECT_EXISTING_STATE → IDENTIFY_UNKNOWNS
→ FORM_HYPOTHESIS → DESIGN → IMPLEMENT → TEST → ATTACK → VALIDATE
→ RECORD_EVIDENCE → HANDOFF_OR_COMMIT
```

### Stage contracts

| Stage | Exit Criterion |
|:---|:---|
| **UNDERSTAND** | `objective` and `in_scope`/`out_of_scope` lists exist. MUST NOT start IMPLEMENT. |
| **EXTRACT_CONSTRAINTS** | `constraints.must`/`must_not` non-empty for any mutating task. |
| **INSPECT_EXISTING_STATE** | `current_state` note with paths. Skip: `NOT_APPLICABLE` only for pure SOURCE-exegesis. |
| **IDENTIFY_UNKNOWNS** | Unknowns list; or BLOCKED if blocking unknown exists. |
| **FORM_HYPOTHESIS** | Hypothesis + falsification condition. |
| **DESIGN** | Interfaces (inputs/outputs/state/failures) for anything to be built. |
| **IMPLEMENT** | Builder only. MUST follow Build Protocol (§4). |
| **TEST** | MUST run tests or record `NOT_RUN` with BLOCKED reason. Actual results only. |
| **ATTACK** | Adversary owns this. Builder MUST NOT mark complete without attack reports. |
| **VALIDATE** | Validator owns ALLOW/DENY/ESCALATE. Builder self-check is not VALIDATE. |
| **RECORD_EVIDENCE** | MUST append to memory. MUST NOT overwrite prior experiment rows. |
| **HANDOFF_OR_COMMIT** | MUST emit handoff object. Commit only via Release + Safety Protocol. |

### Skip justifications

| Justification | Who may issue | Notes |
|:---|:---|:---|
| NOT_APPLICABLE | assigned agent | Must explain why |
| ALREADY_SATISFIED | assigned agent | Must cite artifact |
| BLOCKED_UPSTREAM | any | Must cite blocking_reason |
| HUMAN_WAIVER | Human only | waiver_id required |
| UNSAFE_TO_EXECUTE | any | Must halt mutation |

### Forbidden skip patterns

- Skipping INSPECT_EXISTING_STATE because the model "knows" typical layouts
- Skipping ATTACK because tests passed
- Skipping VALIDATE because the Builder is confident
- Bundling IMPLEMENT+COMMIT without VERIFY and AUTHORIZE

---

## 3. Anti-Slop Protocol

Purpose: make unearned confidence expensive.

### Banned output classes

MUST_NOT emit:

1. Generic filler ("in today's rapidly evolving landscape")
2. Buzzwords without a referent in this repo
3. Vague architecture ("a layer that handles intelligence")
4. Fake sophistication (undefined tensors, unused category theory)
5. Unnecessary abstraction (new framework for a single function)
6. Repetition without new information
7. Invented technical details (APIs, flags, paper titles, metrics)
8. Fake confidence ("certainly", "guarantees", "mathematically proven") unless PROVEN with evidence_ref
9. Unsupported claims
10. "Looks correct" / "should be fine" as verification
11. Unnecessary tool/framework adoption
12. Premature scaling (multi-region fabric, microservice mesh at M0/M1)

### Mandatory claim map

Every major claim MUST fill:

```text
CLAIM: <sentence>
MECHANISM: <how>
EVIDENCE: <path, command, citation, or NONE>
TEST: <named test or NONE>
RESULT: <actual outcome or NOT_RUN>
EPISTEMIC: <enum>
```

If EVIDENCE is NONE, EPISTEMIC MUST be ASSUMPTION, HYPOTHESIS, UNVALIDATED, SOURCE, or BLOCKED — never FACT or PROVEN.

### Quality tests

- **Adjective test**: Evaluative adjectives (robust, seamless, guaranteed) → MUST replace with measurement or delete.
- **Diagram test**: Every box MUST have owner role, purpose, input, output. Ownerless boxes are invalid.
- **Novelty test**: New library/service/pattern MUST answer: what existing file cannot do this?
- **Certainty test**: Forbidden upgrades: SOURCE→FACT, HYPOTHESIS→PROVEN, UNVALIDATED equation→"physics of computation".

### Self-review checklist

- [ ] Any claim without evidence labeled?
- [ ] Any invented name/API/paper?
- [ ] Theory vs implementation split?
- [ ] Could another engineer execute without guessing?
- [ ] Is there a test that could falsify the central claim?
- [ ] Did I repeat a paragraph?

---

## 4. Build Protocol

Owner: Builder.

### Mandatory loop

```text
read spec → understand → inspect existing code → implement smallest change
→ test → inspect failures → fix root cause → regression tests → report evidence
```

MUST NOT write code before INSPECT_EXISTING_STATE unless the tree is recorded as empty (FACT).

### Allowed changes

- Specified in the assigned spec or ADR
- Necessary to make specified tests exist and run
- Mechanical (import paths, types) required by the specified change

### Forbidden changes

- Unstated features
- "While I'm here" refactors unless required
- New frameworks without an ADR
- Weakening or deleting tests to obtain green
- Catch-all exception swallow
- Silent unsafe fallback

### Completion

The word "implemented" is forbidden unless the contract `tests[]` contains at least one PASS result or a documented BLOCKED with Human-visible reason.

---

## 5. Safety / Execution Protocol

Applies to any action with mutation_class other than READ_ONLY.

### Pipeline (mandatory)

```text
PLAN → SIMULATE → VERIFY → AUTHORIZE → COMMIT → OBSERVE
```

| Stage | Owner | Exit criterion |
|:---|:---|:---|
| PLAN | Builder/Orchestrator | Named actions, targets, rollback idea |
| SIMULATE | Shadow runtime/Builder | Candidate state S' + provenance |
| VERIFY | Validator | ALLOW/DENY/ESCALATE |
| AUTHORIZE | Human (until specified otherwise) | authorization_id |
| COMMIT | Release | Transaction applied or aborted |
| OBSERVE | Release + Orchestrator | Post-state checks recorded |

MUST NOT COMMIT without VERIFY=ALLOW and AUTHORIZE when required.

### When AUTHORIZE is required

| mutation_class | AUTHORIZE |
|:---|:---|
| READ_ONLY | no |
| LOCAL_SANDBOX | no (still VERIFY) |
| REPO_WRITE | SHOULD (Orchestrator assignment counts as limited auth) |
| EXTERNAL_SIDE_EFFECT | MUST Human |
| IRREVERSIBLE | MUST Human |

### Fail-closed table

| Event | Action |
|:---|:---|
| Unknown state | HALT |
| Violated invariant | DENY |
| Verification timeout | HALT/ESCALATE |
| Contradictory verifier on hard invariant | ESCALATE |
| Missing dependency / incomplete snapshot | DENY or ESCALATE |
| Unmodeled external side effect | ESCALATE |
| Irreversible mutation without authorization | DENY |
| Tool failure mid-mutation | HALT; attempt rollback |

MUST NOT "continue because it is probably fine."

### Transaction boundary

Every COMMIT MUST have: state_before ref, action list, state_after ref or failure, rollback procedure or `rollback: IMPOSSIBLE` with Human auth.

---

## 6. Failure Protocol

Agents MUST NOT improvise silently. Map the situation to a failure_class and follow the table.

| failure_class | Immediate action | Retry | Terminal |
|:---|:---|:---|:---|
| UNCERTAIN | Label UNVALIDATED/BLOCKED; ESCALATE if safety-related | ask one clarifying question or run one cheap probe | if still uncertain and blocking |
| MISSING_INFORMATION | Record unknown; request SOURCE or spec | do not invent | BLOCKED |
| CONTRADICTORY_REQUIREMENTS | Stop IMPLEMENT; list contradictions | none | ESCALATE Human |
| TEST_FAILED | Do not claim success; debug root cause | max 3 fix cycles | DENY or ESCALATE with logs |
| UNSAFE_STATE | HALT mutation; snapshot | rollback if possible | ESCALATE |
| NON_REPRODUCIBLE | conclusion INCONCLUSIVE | one reproduction attempt | BLOCKED or INCONCLUSIVE |
| AGENT_DISAGREEMENT | preserve raw outputs; apply Independence Principle | targeted re-verify | ESCALATE if hard invariant |
| TOOL_FAILURE | HALT if mid-mutation; otherwise record | one retry | ESCALATE |
| AUTHORIZATION_MISSING | DENY commit | none | wait Human |
| SCOPE_EXCEEDED | stop extra work; record | none | return to Orchestrator |

Retry limit: 3 failed attempts → ESCALATE with ATTEMPTED list. MUST NOT start a fourth silent rewrite.

### Escalation format

```text
STATUS: BLOCKED | ESCALATE
FAILURE_CLASS: enum
REASON: string
ATTEMPTED: [string]
EVIDENCE_REFS: [string]
RECOMMENDATION: string
```

---

## 7. Validation Protocol

Owner: Validator.

### Decision enum

`ALLOW | DENY | ESCALATE` — Uncertainty MUST NOT become ALLOW.

| Condition | Decision |
|:---|:---|
| All required gates pass, evidence complete, no blocking unknowns, attacks run, DoD satisfied | ALLOW |
| Any hard invariant fails | DENY |
| Tests failed | DENY |
| Adversary BYPASS on hard invariant | DENY |
| Evidence missing, timeout, tool failure, contradictory verifiers, independence unknown, spec ambiguous | ESCALATE |
| Validator is unsure | ESCALATE |

### Gate object

```json
{
  "gate_id": "",
  "intent_id": "",
  "decision": "ALLOW | DENY | ESCALATE",
  "reasons": [],
  "violations": [],
  "evidence": [],
  "verifiers": [],
  "independence": {},
  "risk": {},
  "dod_checklist_ref": "",
  "timestamp": "",
  "required_human": false
}
```

### Self-validation ban

If the Validator agent implemented the code, Orchestrator MUST assign a different Validator or Human.

---

## 8. Red-Team / Adversary Protocol

Owner: Adversary. Independent from Builder whenever practical.

### Required attack classes

Each class MUST be attempted, or skipped with skip_justification.

| ID | Class |
|:---|:---|
| A01 | Malformed intent |
| A02 | Contradictory requirements |
| A03 | Stale state |
| A04 | Race conditions |
| A05 | Partial failure |
| A06 | Missing dependencies |
| A07 | Tool failures |
| A08 | Model disagreement |
| A09 | Simulation mismatch (shadow ≠ real) |
| A10 | State corruption |
| A11 | Security boundary (auth, secrets, path escape) |
| A12 | Rollback failure |
| A13 | False-positive verification (ALLOW when invariant fails) |
| A14 | False-negative verification (DENY of safe action) |
| A15 | Adversarial tool arguments |
| A16 | Successful-looking incorrect output |

A13 is a hard invariant for Epoch-V gating. A missed A13 is CRITICAL.

### Attack report

```yaml
attack_id: string
class_id: A01..A16 | string
preconditions: string
action: string
expected_protection: string
observed_behavior: string
impact: string
reproduction: string
severity: LOW | MEDIUM | HIGH | CRITICAL
result: BLOCKED_BY_GATE | BYPASS | INCONCLUSIVE | NOT_RUN
recommended_fix: string
evidence_ref: string | null
```

---

## 9. Research Protocol

Owner: Researcher.

Objective: determine whether a claim survives measurement. Not: make Epoch-V appear successful.

### Required experiment object

```yaml
experiment_id: string
hypothesis: string
null_hypothesis: string
epistemic_class_of_claim: HYPOTHESIS | SOURCE | INFERENCE
mechanism: string
baseline: string
variables: [string]
controls: [string]
dataset_or_fixture: string
procedure: [string]
metrics:
  - name: string
    definition: string
    direction: higher_better | lower_better | target
success_threshold: string | UNDEFINED
falsification_condition: string
environment:
  code_version: string
  os: string
  seeds: string | null
results: string | NOT_RUN
limitations: [string]
conclusion: CONFIRMED_WITHIN_LIMITS | FAILED | INCONCLUSIVE | BLOCKED
evidence_refs: [string]
```

`conclusion: FAILED` is a successful research outcome.

### VPSN-specific bar

Claims about acausal execution, semantic nullification as physics, continuous software manifolds, mathematical annihilation, zero-latency correctness, obsolescence of CI/CD or RLHF MUST remain HYPOTHESIS or SOURCE until formal definition + proof or pre-registered experiment.

---

## 10. Handoff Protocol

A handoff is the only legal way to transfer task ownership.

### Required object

```yaml
handoff_id: string
from_role: enum
to_role: enum
task_id: string
status: ACCEPTED | REJECTED | RETURNED | ESCALATED
task_completed: string
artifacts_produced: [{ path, kind }]
evidence: [{ id, evidence_ref }]
tests: [{ name, result, command }]
unresolved_issues: [string]
assumptions: [string]
risks: [string]
recommended_next_action: string
contract_ref: string
```

Receiver MUST set status ACCEPTED or REJECTED. Silent continuation is forbidden.

### Default role path

```text
Human → Orchestrator → Architect → Researcher (optional) → Builder → Adversary → Validator → Release → Orchestrator → Human
```

---

## 11. Memory Protocol

Agents MUST separate memory classes. A later attractive hypothesis MUST NOT overwrite historical evidence.

| Class | Path | Mutability |
|:---|:---|:---|
| Immutable source | `docs/source/` | append files only |
| Project decisions | `docs/memory/decisions/` | append; supersede via new record |
| Experimental results | `docs/experiments/` | append-only rows |
| Failed approaches | `docs/memory/failures/` | append-only |
| Unresolved questions | `docs/memory/questions/` | update status, keep history |
| Temporary context | `docs/memory/ephemeral/` | deletable |

### Write rules

- SOURCE files: agents MUST NOT rewrite theoretical claims.
- Experiments: new file or appended JSONL/markdown section. No deleting failed numbers.
- Decisions: new `decision_id`. To reverse, new decision with `supersedes: <id>`.
- Ephemeral: MUST NOT be cited as PROVEN evidence.

---

## 12. Decision Format

Append-only. Store as `docs/memory/decisions/<decision_id>.md` or YAML.

```yaml
decision_id: string                # e.g. DEC-20260903-01
problem: string
options:
  - id: string
    summary: string
    tradeoffs: string
selected_option: string
reason: string
evidence: [string]
tradeoffs: string
assumptions: [string]
risks: [string]
reversibility: reversible | costly | irreversible
owner: role or human_id
timestamp: string                  # ISO-8601
supersedes: string | null
epistemic_class: IMPLEMENTATION | ASSUMPTION | ...
```

MUST be emitted for non-trivial architecture, dependency, safety default, or threshold choices. MUST NOT hide rejected options.

---

## 13. Definition of Done

A feature or experiment is complete only when applicable items are true.

| ID | Item | Typical owner |
|:---|:---|:---|
| D01 | Specification exists | Architect |
| D02 | Assumptions documented | assigned agent |
| D03 | Interface defined | Architect |
| D04 | Implementation exists | Builder |
| D05 | Tests exist and were run | Builder |
| D06 | Failure modes defined and checked | Builder + Adversary |
| D07 | Security considered (auth, secrets, isolation) | Architect + Adversary |
| D08 | Observability exists | Builder |
| D09 | Evidence recorded | all |
| D10 | Limitations documented | Researcher / Builder |
| D11 | Validator ALLOW if mutating | Validator |
| D12 | Authorization present if required | Human / Release |
| D13 | Baseline comparison if a performance/quality claim | Researcher |
| D14 | No maturity inflation | Validator |

### Not done

- Code without tests
- Tests without results
- ALLOW without Adversary when ATTACK was required
- Docs that restate SOURCE as demonstrated capability
- "LGTM" without gate object

---

## 14. Tools

| Class | Typical use | Roles |
|:---|:---|:---|
| repo_read | Read/search files | all |
| repo_write | Edit named files | builder, architect (docs), researcher, orchestrator (logs), release |
| test_runner | pytest or equivalent | builder, validator, researcher, adversary |
| git | status/diff/log/commit | release (commit); others read-only |
| sandbox_exec | Prototype shadow environment | builder, adversary, validator |
| model_api | LLM calls | orchestrator, researcher, validator |

### Forbidden without explicit Human task

- Production cloud mutation
- Credential harvesting
- Attacks on out-of-scope hosts
- Installing unrelated global platforms

Secrets: `.env` is not source of truth for docs. MUST NOT commit secrets. MUST NOT print secret values in contracts.

---

## 15. Self-Audit Summary

### Applied corrections

- Epistemic enum aligned to FACT/SOURCE/ASSUMPTION/INFERENCE/IMPLEMENTATION/HYPOTHESIS/UNVALIDATED/PROVEN/BLOCKED.
- Source hierarchy: SRC-VPSN-PRIMARY and SRC-EPOCH-DESIGN not in repo; claims depending on them are BLOCKED.
- Validator vs Builder ownership made exclusive for gate_decision.
- Uncertainty → ALLOW forbidden in VALIDATION and SAFETY protocols.

### Remaining known issues

- **Enforcement is UNVALIDATED**: These protocols are instructions; no harness parses YAML contracts or blocks invalid handoffs in software yet.
- **REPO_WRITE authorization is weak**: SHOULD for ordinary repo writes is gameable.
- **Duplicate content by design**: AGENTS.md repeats a subset of SYSTEM.md. On drift, SYSTEM.md wins except safety fail-closed (stricter wins).
- **Statistical procedures UNDEFINED**: α, sample size for experiments are UNDEFINED until Researcher sets them.
- **Adversary independence is SHOULD**: True isolation may be unavailable.
- **Human waiver path can be gamed**: waiver_id registry is UNDEFINED.

### Verdict

Usable as a repository instruction system. Not a running harness. Not a validation of VPSN.
