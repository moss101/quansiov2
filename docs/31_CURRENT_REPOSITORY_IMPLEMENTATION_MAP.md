# 31 — Current repository implementation map

This map gives implementation agents concrete placement guidance for the currently observed application tree. It does not grant completion credit; each path must satisfy the canonical task assertions.

| Current path | Required disposition | Implementation instruction |
|---|---|---|
| `main.py`, `core/main.py`, `core/websocket/handler.py` | MIGRATE | Converge public entrypoints behind `quansio-api`; remove client-supplied canonical user/tenant authority; generated command/event contracts replace hand-authored task truth. |
| `core/auth/`, `core/config.py` | MIGRATE | Move durable identity/session/RBAC/policy ownership to `quansio-control` and authoritative storage; remove process-local/example-account authority from production reachability. |
| `core/orchestrator/main.py`, `core/agents/`, `core/tools/integration.py` | FREEZE_THEN_REMOVE as authority | Extract reusable domain logic only; WorkGraph/AgentGraph/StateGraph plus GraphTransaction become the sole runtime execution path. |
| `core/tools/integrations/` | REUSE_BEHIND_OWNER | Retain useful protocol translation behind `quansio-model-gateway` or `quansio-integration-broker`; remove direct credential custody and any simulated success from production. |
| `core/context/`, `core/memory/`, `core/learning/` | MIGRATE | Consolidate into Context Projection, Knowledge Fabric and Controlled Skill Evolution; eliminate memory-as-recovery and competing semantic stores. |
| `core/tools/code_executor.py`, `core/tools/simple_tools.py` | MIGRATE | Host/process/browser helpers must execute through `qworkerd` and machine/browser canonical paths with capability/effect controls; direct host execution is not the production sandbox. |
| `core/tools/api_integration.py`, `core/tools/advanced/` | REUSE_BEHIND_OWNER | Migrate connector operations to canonical Tool Registry and integration broker; consequential calls require EffectRecord. |
| `core/tools/file_system.py` and storage helpers | REUSE_BEHIND_OWNER | File operations become artifact/tool operations with tenant scope, grants, digests and evidence. |
| `frontend/index.html`, `frontend/index_enhanced.html` | MIGRATE | Existing views may inform UI behavior, but supported clients must use canonical command/event projection and cannot own execution state. |
| indexer owner | CANONICAL (implemented) | `quansio/indexer` (ingest/chunk/freshness/tombstone/rebuild) exposed by the `quansio-indexer` service HTTP surface (`quansio/indexer/app.py`). |
| worker gateway | CANONICAL (implemented) | `quansio/worker_gateway` (governed transfers, endpoint relay, browser sessions/observations) exposed by the `quansio-worker-gateway` service (`quansio/worker_gateway/app.py`). |
| machine control | CANONICAL (implemented) | `quansio/machine_control` (inventory, placement/lease/fence, durable deliveries, isolated task runtimes, workspace computers, checkpoints, private targets) exposed by the `quansio-machine-control` service (`quansio/machine_control/app.py`). |
| artifact service | CANONICAL (implemented) | `quansio/artifact` (digest-addressed immutable store over MinIO + PostgreSQL metadata, scan states, restore verification) exposed by the `quansio-artifact` service (`quansio/artifact/app.py`). |
| notification service | CANONICAL (implemented) | `quansio/notify` (durable attention delivery, receipts, outage recovery) exposed by the `quansio-notify` service (`quansio/notify/app.py`). |
| integration broker | CANONICAL (implemented) | `quansio/integration_broker` (mediated connector operations over credential handles + authorized EffectRecords, HMAC webhook ingress with exactly-once work resume) exposed by the `quansio-integration-broker` service (`quansio/integration_broker/app.py`). The Tool Registry remains control-owned (`quansio/control/connectors.py`). |
| desktop/mobile/CLI supported clients | CANONICAL (implemented as thin projections) | `clients/cli` (packaged `quansio` CLI over canonical APIs), `clients/web` (chat-first canonical command/event projection; browser-qualified), `clients/desktop` (Electron shell around the web projection; code-verified, GUI launch via `npm install && npm start`), `clients/mobile` (attention/continuation PWA; browser-qualified against live services). Shared convergence engine in `clients/pyapp`. Clients own no execution/task/model authority; acceptance: `tests/uxclients`, `tests/services`, browser qualification transcripts. |

Before deleting or moving any current path, identify active consumers, data compatibility, rollback and the task that proves canonical replacement. The final architecture gate must prove no conflicting production path remains reachable.
