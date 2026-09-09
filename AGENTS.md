# AGENTS.md — Binding implementation rules

## Mission
Implement the entire Quansio product defined by this authority as production software. Do not optimize for a demo, superficial feature count, or documentation completion.

## Canonical-owner rule
Before adding state or behavior identify: owner service, canonical schema, command, durable store, RuntimeEvent, capability, policy, effect class, idempotency, cancellation, recovery and qualification. If ownership is unclear, resolve it before coding.

## One-core rule
Never create a second orchestrator, swarm scheduler, research runtime, business runtime, memory system, skill runtime, model router, browser stack, policy engine, approval authority, effect path, durable task store or recovery system. Logical services may be physically co-located early, but ownership and interfaces remain canonical.

## Real implementation rule
Production acceptance cannot rely on mocks, fake persistence, simulated provider success, placeholder handlers, hard-coded success, skipped release tests, suppressed security failures, client-owned task truth or alternate direct provider/connector/effect paths. Unit-test doubles are allowed only within tests whose acceptance contract permits them.

## Evidence rule
Cryptographic report signatures are not required. Evidence is accepted through reproducibility: exact task/requirement/assertion coverage, reachable repository commit, executed verification report, actual artifact digests, environment identity, real-boundary proof when required, and rollback/recovery proof when required. `BLOCKED_REAL_BOUNDARY` is a non-completing state.

## Change discipline
Follow the task DAG. Do not silently weaken requirements or acceptance assertions. Any architecture change affecting an invariant, owner, durable schema, security boundary, external effect or release transition requires a decision record with context, alternatives, risk, migration/rollback and review trigger.

## Continuous execution loop
READ → TASK-SPECIFIC RECONCILIATION → PLAN → IMPLEMENT → MIGRATE → TEST POSITIVE → TEST ADVERSARIAL → TEST RECOVERY → VERIFY SECURITY/OBSERVABILITY → PRODUCE EVIDENCE → VALIDATE → NEXT DAG-READY TASK.
