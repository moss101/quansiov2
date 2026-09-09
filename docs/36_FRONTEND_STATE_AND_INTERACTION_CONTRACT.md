# 36 — Frontend state and interaction contract

## Canonical client store slices
- identity/session projection
- workspace/agent directory projection
- work/run graph projection
- timeline/event cursor
- attention/approval projection
- artifact/evidence projection
- research records/progress
- browser/computer session/controller state
- installed business capabilities/skills read model
- automation schedules/fire history
- support/health projection

Every slice stores server object revision/cursor. Optimistic UI may show `PENDING_COMMAND` but cannot locally convert to canonical success before server event/response.

## Interaction safety
- Consequential buttons display semantic action, target and scope from server-normalized proposal.
- Approval response includes request identity; server revalidates scope/current state.
- Takeover controls show current controller and pending acquisition.
- Offline mode disables commands that cannot safely queue with idempotency; safe commands explicitly show queued state.
- Reconnect performs snapshot/cursor catch-up before enabling stale-state-sensitive commands.

## Performance
Virtualize long timelines, paginate artifacts/research records, stream incremental worker/model/research progress, and keep visual streaming separate from canonical task mutation. UI performance optimizations must not discard authoritative event identity needed for reconciliation.
