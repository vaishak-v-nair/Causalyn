# Additional schemas (compact)

See also `enums.yaml`, `agent_contract.yaml`.

## handoff.yaml

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

## gate_decision.yaml

```yaml
gate_id: string
intent_id: string
decision: ALLOW | DENY | ESCALATE
reasons: [string]
violations: [string]
evidence: [string]
verifiers: [object]
independence: object
risk: object
dod_checklist_ref: string
timestamp: string
required_human: boolean
```
