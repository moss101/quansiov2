# 12 — Tools, approvals and external effects

## Tool fidelity
A tool can be technically callable while unsuitable for a business capability. Fidelity is explicit: lossless, constrained-lossless, degrading, irreversible, human-only or unsupported.

## Consequential path

```text
Tool proposal / semantic action
          |
          v
CapabilitySnapshot
          |
PolicyDecision + privacy + sequence guard
          |
ApprovalRequest if required
          |
EffectRecord
          |
Actuator / Integration Broker / Browser / Machine
          |
Receipt + evidence
          |
Settlement / reconciliation
```

Effect states: `PROPOSED`, `APPROVAL_REQUIRED`, `APPROVED`, `EXECUTING`, `UNKNOWN`, `COMMITTED`, `DENIED`, `FAILED`, `RECONCILED`.

## Exact-scope approvals
Approval binds semantic operation/effect/normalized argument digest/target/risk/expiry. Financial scope additionally binds payee, amount in minor units, currency, purpose, funding handle, per-effect ceiling and cumulative budget. Changing amount by one minor unit or changing payee invalidates the receipt.

## UNKNOWN
After an ambiguous timeout the system must not retry blindly. It queries provider/target state using original idempotency/effect identity, records reconciliation, and only retries if that evidence proves no effect occurred and the operation is safe to retry.
