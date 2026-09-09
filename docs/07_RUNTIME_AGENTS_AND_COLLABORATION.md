# 07 — Runtime, agents and collaboration

## Graph model
- `WorkGraph`: executable work nodes/edges/dependencies/deadlines/state.
- `AgentGraph`: persistent/ephemeral participants, ownership, workspace and admitted capabilities.
- `StateGraph`: canonical state facts/projections required by execution.
- `GraphTransaction`: sole atomic mutation contract over graph/runtime state.

## Worker admission
Admission atomically reserves capacity, budget, child CapabilitySnapshot and target constraints before dispatch visibility. Failure before dispatch releases reservation; recovery resolves the original admission idempotently.

## Fan-out/fan-in
Child turns are asynchronously dispatched. Every dispatch/outcome is durable independently. Parent can continue, wait, aggregate partial results or cancel. At least 32 concurrent child reservations/outcomes are exercised in qualification.

## Cancellation
Parent cancellation prevents queued children, requests cancellation of active cancellable children, preserves already committed external effects, releases eligible reservations and returns explicit partial outcomes. Recovery resumes cancellation state, not the original parent plan.

## Durable waits
Timers, approvals, questions and callbacks store wait identity/state and free the process. Duplicate callback delivery is idempotent. Runtime restart restores waits from protocol state.

## Client independence
Closing every interactive client does not terminate eligible work. Reconnecting clients receive current snapshot/cursor and worker outcomes completed while clients were absent.
