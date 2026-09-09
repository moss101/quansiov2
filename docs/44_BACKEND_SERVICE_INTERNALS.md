# 44 — Backend service internals and package layout

The canonical service names define ownership, not a requirement that every owner starts as an independently deployed process. Early deployment may co-locate owners, but packages, persistence boundaries and interfaces must preserve the final ownership model so extraction does not require rewriting authority.

## Recommended repository layout

```text
cmd/
  quansio-api/
  quansio-control/
  quansio-runtime/
  quansio-model-gateway/
  quansio-context/
  quansio-indexer/
  quansio-worker-gateway/
  quansio-machine-control/
  quansio-integration-broker/
  quansio-artifact/
  quansio-notify/
  qworkerd/
internal/
  auth/
  control/
  runtime/
  modelgateway/
  context/
  indexer/
  workers/
  machines/
  integrations/
  artifacts/
  notifications/
  policy/
  effects/
  observability/
generated/
  contracts/
migrations/
clients/
deploy/
tests/
```

Equivalent language-specific organization is acceptable if canonical imports and owner rules remain mechanically enforceable.

## Request admission

`quansio-api` authenticates transport identity, resolves tenant/workspace/session from server state, validates canonical command revision/idempotency, applies coarse request limits and forwards the command to its owner. It does not call model providers, connectors or guest actuators.

`quansio-control` owns mutable administrative truth and emits versioned snapshots/decisions. Runtime steps bind exact IDs/revisions at admission rather than re-reading mutable configuration midway through an effect.

## Runtime transaction boundary

A runtime transition loads expected graph/agent/state revisions, validates preconditions, applies GraphTransaction, persists protocol changes, appends RuntimeEvent/outbox and commits atomically. External providers are never called while a database transaction is held. External effects use the Effect Ledger state machine around actuation.

## Concurrency

Use optimistic revision checks or row-level locks only at the canonical aggregate boundary. Worker admission and budget reservation must be atomic. Run/step transitions are idempotent by transaction/command identity. Duplicate network delivery never means duplicate state mutation.

## Internal APIs

Internal APIs use generated canonical contracts plus service-specific typed requests where the request is not a durable/wire authority object. Do not share mutable in-memory runtime objects across owners as a hidden internal API. Timeouts, cancellation, trace IDs and tenant identity propagate across calls.

## Error handling

Expected failures are typed domain outcomes. Unexpected errors are observable failures, not success fallbacks. Services must not catch broad exceptions and synthesize empty/default success. Retries are bounded, jittered where appropriate and only used for operations whose idempotency/reconciliation contract permits them.

## Deployment health

Each deployable exposes liveness separately from readiness. Readiness checks owner-critical dependencies and migrations/configuration. A process can remain live while being unready. Readiness failure must not route new work into a service that cannot safely satisfy its owner contract.
