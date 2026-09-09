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
| indexer owner | BUILD | Implement dedicated ingestion/index/freshness/tombstone owner. |
| worker gateway | BUILD | Implement authenticated typed worker/guest transport, lease/generation/fence and ACK/redelivery. |
| machine control | BUILD | Implement target inventory, placement, lifecycle, checkpoints, restore and migration authority. |
| artifact service | BUILD | Implement immutable artifact/evidence metadata, digest verification, scanning/grants/lifecycle. |
| notification service | BUILD | Implement durable attention delivery without approval/task authority. |
| desktop/mobile/CLI supported clients | BUILD | Implement the defined client surfaces over canonical server APIs/events. |

Before deleting or moving any current path, identify active consumers, data compatibility, rollback and the task that proves canonical replacement. The final architecture gate must prove no conflicting production path remains reachable.
