# 47 — qworkerd guest protocol and execution boundary

`qworkerd` is a constrained actuator, not an agent brain. It does not own task truth, policy, credentials, model routing or durable business state.

## Session establishment

The worker gateway presents a target-bound session token/transport identity. `qworkerd` validates target identity, execution generation and lease/fence context before accepting operations. Session renewal cannot lower the fence or resurrect an expired generation.

## Operation envelope

Guest operations carry:

```text
operation_id / version
request_id / delivery_id / idempotency_key
tenant + target
execution_generation
lease_id + fence_token
capability_snapshot_id
policy/effect references where consequential
timeout/cancellation identity
arguments
```

The guest rejects stale generation/fence before invoking filesystem/process/browser actuators.

## Filesystem

Mounts are explicit and task/workspace scoped. Protected paths are denied unless the admitted capability permits them. Artifact inputs are digest-verified before use. Outputs become artifacts through the artifact service rather than escaping as untracked guest paths.

## Process/terminal

Commands use typed executable, argv, cwd, environment overlay, stdin mode, timeout, output limits and streaming identity. Shell string execution is not the default contract. Secret handles are materialized only for the exact operation when unavoidable and are scrubbed from logs/output.

## Network

Egress is deny-by-default and policy-controlled. DNS, TCP/HTTP proxy and browser traffic are attributable to target/run/operation. Internal control-plane addresses are not reachable unless explicitly part of the guest protocol.

## Delivery

A completed operation is stored under idempotency/delivery identity before ACK. Lost ACK causes result redelivery, not re-execution. Ambiguous host-side consequential effects follow the Effect Ledger reconciliation contract.
