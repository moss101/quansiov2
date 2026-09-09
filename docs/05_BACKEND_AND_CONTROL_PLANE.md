# 05 — Backend and control plane

## API
Public commands authenticate first, resolve server-owned tenant/user/workspace/session identity, validate schema/revision/idempotency and dispatch to canonical owner. APIs do not accept client assertions of completed task/effect/approval truth.

## Control plane
Owns tenant configuration, users/roles, policies, approvals, skill/business/tool registries, automation definitions, support selection and administrative configuration. Runtime consumes versioned snapshots/decisions rather than reading mutable client configuration directly mid-step.

## Runtime
Owns graph execution, waits, worker lifecycle, cancellation, budget reservation, model/tool requests and recovery coordination. Every durable transition produces canonical event/protocol state through transaction boundaries.

## Integration broker
Owns connectors and webhooks. Credentials are brokered as scoped handles. Consequential operations require EffectRecord; adapters cannot invoke external state changes from an unmediated helper path.

## Artifact service
Stores immutable content/evidence by digest, scan state, tenant, provenance and grants. Artifacts can be referenced by tasks/research/effects without embedding large bytes in canonical event payloads.
