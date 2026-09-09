# Stable error families

- `AUTH_*` authentication/session/tenant failure
- `CAP_*` capability admission or narrowing failure
- `POLICY_*` policy/privacy/residency denial
- `APPROVAL_*` approval absent/expired/scope mismatch
- `EFFECT_*` effect proposal/execution/reconciliation failure
- `MODEL_*` provider/routing/stream/usage failure
- `RESEARCH_*` retrieval/verification/program failure
- `WORKER_*` worker admission/delivery/cancellation failure
- `MACHINE_*` target/lease/generation/fence/snapshot failure
- `BROWSER_*` structured action/takeover/session failure
- `ARTIFACT_*` digest/grant/scan/lifecycle failure
- `AUTOMATION_*` schedule/fire/authority failure
- `CONTRACT_*` schema revision or canonical contract mismatch

Errors identify operation/request/run context, retryability and safe human message. Secret or protected payload content is never added merely for diagnostics.
