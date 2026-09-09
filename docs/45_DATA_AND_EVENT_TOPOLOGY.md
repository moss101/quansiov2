# 45 — Data, event and messaging topology

## Authoritative relational state

PostgreSQL is the default authoritative relational store. Equivalent production technology requires an architecture decision and qualification. Minimum logical tables/aggregates include:

```text
tenants, users, memberships, workspaces, sessions
agents, agent_profiles
runs, workgraphs, workgraph_nodes, workgraph_edges
agentgraphs, stategraphs, graph_transactions
runtime_events, transactional_outbox, protocol_state
capability_snapshots, policy_decisions
approval_requests, approval_receipts
effects, effect_attempts, effect_receipts
budget_reservations, usage_settlements
automations, automation_fires
execution_targets, worker_leases, machine_checkpoints
browser_sessions, controller_leases
skills, skill_versions, skill_evaluations
business_capability_packs, capability_evaluations
tool_registry, connector_registry
support_selections, qualification_results, release_candidates
```

Table names may vary, but the ownership and durability represented above may not disappear into process memory.

## Runtime events

Canonical RuntimeEvents are immutable append records. A transactional outbox publishes them to the durable event transport after commit. The transport is a delivery mechanism, not the sole truth. Consumers deduplicate by `event_id` and track owner-specific projection cursor/checkpoint.

Suggested subject families:

```text
runtime.events.<tenant-shard>
worker.commands.<target-or-pool>
worker.results.<tenant-shard>
notifications.<tenant-shard>
index.ingest.<tenant-shard>
webhooks.<connector-family>
```

Subjects do not encode untrusted client tenant values directly; routing identity is server-resolved.

## Cache/lease store

Redis or equivalent may store short-lived leases, rate-limit counters and reconstruction-safe caches. Flushing cache must not lose canonical work, approvals, effects or scheduled definitions. Lease recovery revalidates authoritative generation/fence before actuation.

## Object/evidence storage

Large artifacts, browser captures, research evidence, checkpoint objects and exported reports live in object storage by immutable digest/versioned manifest. Database rows reference digest and grant metadata. Object bytes are never silently overwritten under a historical digest identity.

## Data retention

Retention is category-specific. Canonical effect/audit/evidence retention follows business/legal policy. Cache and projections can expire earlier because they are reconstructible. Deletion requests are themselves governed operations and must respect legal hold/retention constraints.

## Database migrations

Use expand/contract for rolling compatibility where practical. Candidate qualification binds the exact migration set digest. A migration that cannot roll back must have explicit forward-recovery and backup restore evidence before canary. Schema drift between application binaries and database is a readiness failure.
