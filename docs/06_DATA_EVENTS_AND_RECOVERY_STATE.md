# 06 — Data, events and recovery state

## Storage classes
| Class | Purpose | Authority |
|---|---|---|
| Relational authoritative store | identities, agents, runs, graphs, protocol state, approvals/effects/schedules/registries | authoritative |
| Durable event transport | outbox delivery, work/event notifications | transport; not sole truth |
| Cache/lease store | acceleration, leases, bounded ephemeral coordination | non-authoritative |
| Object/evidence store | immutable artifacts/evidence/checkpoint blobs | authoritative for referenced bytes |
| Search indexes | derived retrieval projections | rebuildable |

Every durable schema has migrations, ownership, tenant scoping, backup/restore and retention.

## Event rules
`RuntimeEvent` carries stable event identity, tenant/workspace/run, canonical sequence, causal parent(s), producer identity/sequence, execution generation, occurred time, commit time and versioned payload. Canonical sequence determines replay; wall-clock timestamps do not.

## Protocol state
Persist tool calls, approval/question waits, worker dispatch/outcome, browser/controller state, endpoint delivery/ACK, cancellation and durable timers. Exact resume does not depend on semantic memory.

## Recovery consistency
A production recovery point binds database position, RuntimeEvent sequence, evidence manifest digest, snapshot inventory digest, effect-settlement watermark and unresolved UNKNOWN effect IDs. Reopening consequential execution requires a compatible point and reconciliation of ambiguous effects.
