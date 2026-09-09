# 43 — Frontend component architecture

## Technology profile

Primary desktop: Electron + React + TypeScript. Web uses the same React domain packages where browser-safe. Mobile may use a native or cross-platform shell, but shares generated contracts, event reducers and domain rules rather than duplicating authority. CLI uses generated API/event bindings and remains a thin client.

## Package boundaries

```text
clients/
  desktop/
    main/                 Electron main process
    preload/              minimal typed IPC bridge
    renderer/             React application
  web/
  mobile/
  cli/
packages/
  contracts-generated/    generated from canonical schemas
  client-api/             HTTP/RPC + stream client
  projections/            pure RuntimeEvent reducers
  ui-domain/              shared domain view models
  design-system/          tokens/components/accessibility primitives
```

Renderer code must not receive Node.js ambient authority. Desktop preload exposes only explicitly typed capabilities such as secure local file selection, notification bridge and approved local-target integration. `contextIsolation` remains enabled and arbitrary renderer-to-main command execution is prohibited.

## Route and surface model

- `/workspace/:workspaceId` — default workbench and active teammate context.
- `/work/:runId` — WorkGraph/timeline, worker outcomes, artifacts and evidence.
- `/research/:runId` — ResearchRecords, source/evidence panes and verification state.
- `/browser/:sessionId` — embedded managed browser/computer surface with controller state.
- `/capabilities` — qualified Business Capability Packs, installation and evaluation detail.
- `/skills` — qualified skill versions, evaluation and rollback metadata for authorized users.
- `/automations` — definitions, next logical fire, fire history and pause/resume/delete.
- `/approvals` — pending and historical ApprovalRequests with exact semantic scope.
- `/admin/*` — tenant/RBAC/policy/support/environment management.

## Projection store

Every server-owned slice is revision/cursor based. Reducers are deterministic and idempotent. The client stores:

```text
IdentityProjection
AgentDirectoryProjection
WorkProjection
TimelineProjection
AttentionProjection
ArtifactProjection
ResearchProjection
BrowserSessionProjection
CapabilityCatalogProjection
AutomationProjection
SupportProjection
```

A reducer may ignore an already-applied event ID but may not invent a canonical event or mark a server operation complete optimistically. Commands use an explicit local `PENDING_COMMAND` envelope until the server response/event confirms accepted state.

## Reconnect algorithm

1. Freeze stale-state-sensitive actions.
2. Re-authenticate/refresh session if necessary.
3. Request current snapshot revision and server cursor.
4. Apply missed RuntimeEvents from last durable client cursor.
5. If cursor is invalid/compacted, replace projection with authoritative snapshot, then continue streaming.
6. Reconcile pending idempotent commands by command ID.
7. Re-enable actions only after `CAUGHT_UP`.

## Work timeline

Timeline entries are projections of user commands, agent turns, worker dispatch/outcomes, model/tool state, approval waits, effects, artifacts and recovery events. Wall-clock time is display metadata; canonical sequence controls ordering. Parallel branches remain visibly related by causal parent rather than being flattened into misleading timestamp order.

## Browser/computer surface

The live surface contains session identity, target state, current controller, takeover request, return-control action, structured observation status, visual stream status and effect/approval state. Human takeover does not create a new browser session. Returning control requires the agent to re-observe before continuing.

## Approval UX

Approval cards display normalized semantic operation, target, exact arguments/scope digest, relevant data classification, amount/payee for financial effects, expiration and risk explanation. UI never derives approval scope from a button label; it renders the server-owned ApprovalRequest.

## Loading/error states

Every page has explicit `INITIAL_LOADING`, `READY`, `EMPTY`, `DEGRADED`, `RECONNECTING`, `FORBIDDEN`, and `FAILED` states as applicable. A dependency outage may degrade one pane without rewriting canonical task state. Errors expose safe retry/cancel/reconnect actions only when allowed by the server error contract.

## Accessibility and quality

Core flows are keyboard complete, focus order is deterministic, live regions are rate-limited, state is never color-only, reduced motion is honored and virtualized lists preserve accessible position. Desktop and web qualification include keyboard-only approval, work creation, cancellation, artifact open and browser takeover flows.
