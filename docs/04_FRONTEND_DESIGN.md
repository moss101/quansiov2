# 04 — Frontend design

## Desktop workbench

```text
+--------------------------------------------------------------------------------+
| Workspace / Search / New Work / Teammate                         Health Account |
+------------------+--------------------------------------+----------------------+
| Teammates        | Work / Conversation / Timeline       | Attention / Context  |
| Tasks            | - canonical event stream             | - approvals          |
| Research         | - worker partial outcomes            | - questions          |
| Capabilities     | - tool/effect states                 | - evidence           |
| Automations      | - artifacts and citations            | - budgets/policy     |
+------------------+--------------------------------------+----------------------+
| Artifact / Live Browser / Computer Workspace                                   |
| session identity | observe/takeover/return | target health | controller state   |
+--------------------------------------------------------------------------------+
```

### State model
- Initial load: authenticated snapshot + canonical event cursor.
- Incremental updates: ordered RuntimeEvent stream. Duplicate delivery is idempotent; out-of-order events are buffered/reconciled by canonical sequence.
- Local persistence: cache/preferences only. It never becomes task/approval/effect truth.
- Connection states: `ONLINE`, `RECONNECTING`, `CAUGHT_UP`, `DEGRADED`, `OFFLINE`.

### Key flows
1. **Create teammate:** identity/profile → permitted knowledge/workspace bindings → capabilities → create persistent agent → show durable identity.
2. **Start work:** command → WorkGraph → runtime events → workers/tools/models/effects → incremental timeline.
3. **Approval:** render exact semantic scope → approve/deny request identity → server revalidates scope/current policy → resume or deny.
4. **Research:** program progress → candidate/record/evidence panes → source verification → synthesized artifact.
5. **Business capability:** browse qualified pack → inspect requirements/policy/evals → install → execute through normal work path.
6. **Takeover:** request controller lease → show ownership → human acts → return lease → agent re-observes current state before continuing.

### Accessibility
Keyboard-complete core flows, deterministic focus movement, assistive labels, reduced-motion behavior, no color-only state, accessible live-region updates for critical attention without overwhelming streaming deltas.
