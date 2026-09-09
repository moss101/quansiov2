# 32 — Agent implementation playbook

## Per-task preflight
1. Read the independent requirement statements and assertion IDs.
2. Read task positive/negative/recovery assertions and dependencies.
3. Inspect current code paths and classify only the task-specific state.
4. Confirm service owner, schemas, migrations, commands/events, effects, support profile and real-boundary requirement.
5. Plan removal/migration of conflicting reachability before adding another path.

## Coding rules
- Write production code and tests in the owning package/service.
- Durable state changes include migration and repository implementation.
- Cross-service communication uses canonical contracts, not shared mutable in-process objects.
- Generated bindings are regenerated from schemas; do not hand-fork them.
- Consequential browser/connector/tool operations enter Effect Ledger before actuator call.
- Model calls enter model gateway; provider adapter cannot see higher-level orchestration state beyond the envelope.
- Target actions validate tenant + generation + lease + fence + capability + policy + effect.

## Verification rules
Run the smallest affected tests continuously, then the task's complete positive/adversarial/recovery suite. Real-boundary tasks use a real test boundary. Record exact commands, environment and artifacts. Run authority/contract/source/evidence validators before setting task completion.

## Failure behavior
Do not convert a failure to success by broad exception handling, default data, mock fallback or disabling a check. Persist typed failure/unknown state where the contract requires it. If an external boundary is unavailable, record `BLOCKED_REAL_BOUNDARY` and proceed only with DAG-ready work that does not depend on it.

## Reporting
For each work unit: task ID, assertions, files/migrations changed, tests/commands/results, evidence path, blockers and next DAG-ready task. Keep reports concise; implementation work has priority over commentary.
