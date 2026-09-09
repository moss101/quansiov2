# 22 — Deployment and environments

Minimum production-like qualification topology contains the authoritative relational store, durable event transport, cache/lease store, object/evidence storage, API/control/runtime, model gateway, context/indexer, worker gateway, machine control, integration broker, artifact/notification services and at least one enabled real execution/browser/model boundary.

Each environment has a stable environment identity, configuration digest, tenant-isolated test identities, health checks and teardown. Qualification never silently substitutes in-memory components for required durable boundaries.

Logical services can share a process during early build only when canonical interfaces/owners remain explicit and tests prove no direct cross-owner state mutation. Production deployment topology must be generated from registered deployables and support selection.

Secrets are provided through environment/secret management or brokered handles, not committed configuration. Provider credentials exist only in model-gateway scope; connector credentials remain behind integration-broker/broker scope.
