# 13 — Security, privacy and authority

## Security chain
`authenticated actor → CapabilitySnapshot → PolicyDecision → privacy classification → sequence guard → scoped credential handle → approval/effect as required → actuator`

### Capability
Snapshot is immutable for an admitted step and carries explicit atoms/constraints/expiry/parent. Child snapshots are strict subsets.

### Policy
Decision binds actor, capability, operation, normalized arguments, target, data class and policy revision. Argument change requires a new decision.

### Privacy
Before remote model/connector/upload/worker egress, classify sensitive data and apply destination-aware allow/redact/approval/deny. A denied path sends zero protected bytes.

### Credentials
Secret material remains behind brokered handles. Handles are short-lived and operation/target/tenant scoped. Guests and clients cannot request reusable plaintext credential material.

### Sequence guard
Rules can identify dangerous combinations across canonical events/effects. A later operation may be denied/escalated based on earlier authorized activity.

### Tenant isolation
Enforce at API, repository, event stream, object/evidence, context, model, connector, worker, machine and client cursor boundaries. Fail closed when authoritative security state is unavailable.
