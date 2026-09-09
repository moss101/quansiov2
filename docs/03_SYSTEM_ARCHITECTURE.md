# 03 — End-to-end system architecture

```text
Clients
Desktop | Web | Mobile | CLI | Admin
             |
             v
        quansio-api
             |
       quansio-control
             |
        quansio-runtime
   /          |           \
  v           v            v
Context    Model Gateway   Effect Path
  |           |            |
Indexer    Model Profiles  Integration Broker
  |                        |
Artifact <-----------------+
  ^                        |
  |                        v
Worker Gateway ------> Machine Control
                           |
                           v
                         qworkerd
                  isolated/persistent/private targets

Control/Runtime ------> quansio-notify
All owners -----------> canonical events/telemetry/evidence
```

## Canonical owners

| Owner | Owns | Must not own |
|---|---|---|
| `quansio-api` | Authenticated public commands, session entry, event projection, upload initiation. | No graph execution, provider credential custody, effect settlement, or machine actuation. |
| `quansio-control` | Tenant/identity/RBAC/policy/approval/registry/schedule/support configuration authority. | No model, browser, connector, or guest actuation. |
| `quansio-runtime` | Canonical WorkGraph/AgentGraph/StateGraph execution, admission, turns, waits, cancellation, budgets, recovery coordination. | No direct provider credentials or unmediated external effects. |
| `quansio-model-gateway` | All model fulfillment, provider adapters, routing, streaming, usage settlement, model egress policy. | No task truth, user approval truth, or general connector authority. |
| `quansio-context` | Context Projection, SearchProgram execution, retrieval coordination, evidence assembly, Knowledge Fabric queries. | No independent task scheduler or effect path. |
| `quansio-indexer` | Ingestion, chunking, indexing, freshness, tombstones and index provenance. | No model orchestration or business workflow authority. |
| `quansio-worker-gateway` | Authenticated worker/guest transport, lease/generation validation, ACK/redelivery and cancellation relay. | No tenant policy ownership or model credentials. |
| `quansio-machine-control` | Execution-target inventory, placement, leases, generations, snapshots, restore and migration. | No application task truth or provider fulfillment. |
| `quansio-integration-broker` | Connector adapters, credential handles, typed external operations and webhook ingress. | No policy/effect bypass; no ambient tenant secret exposure. |
| `quansio-artifact` | Immutable artifacts/evidence, digests, scanning, grants and lifecycle. | No task orchestration. |
| `quansio-notify` | Durable attention/notification delivery and receipt tracking. | No approval truth or task state authority. |
| `qworkerd` | Guest actuator for assigned filesystem/terminal/browser/computer/process operations. | No ambient cloud authority, provider credentials, or tenant policy ownership. |

Logical services may share a deployable during early implementation only when ownership, schema and interfaces remain explicit and tests prove no hidden alternate authority. Scaling or extraction must not change semantics.

## Trust boundaries
- Interactive clients: untrusted for canonical identity fields; authenticate and receive scoped server authority.
- Public API/control: validates identity/tenant/policy commands; does not execute provider/tool/machine actions directly.
- Runtime: authoritative orchestration and state transition boundary.
- Model gateway: provider credential and provider protocol boundary.
- Integration broker: connector credential handle and external operation boundary.
- Worker/machine fabric: task-scoped execution boundary with generation/lease/fence.
- Artifact/evidence: immutable content/digest boundary.
