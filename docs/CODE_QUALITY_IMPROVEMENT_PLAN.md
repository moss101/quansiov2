# Code-quality improvement plan

Date: 2026-09-11. Baseline commit: `d4facfa7f8b1af07d4eef4fc6338205abeafbe6d`. The working tree was clean before this planning update.

Status: proposed implementation backlog. This document does not change canonical tasks, acceptance assertions, service ownership, or completion status.

The first priority is correctness at transaction and service boundaries. Next, make builds and verification reproducible, strengthen canonical contract typing, and refactor the most consequential code in small, independently verified changes.

## Baseline and limitations

The repository has a canonical task DAG, generated contracts, real-environment fixtures, and substantial integration tests. Preserve those foundations.

Observed checks:

- `scripts/validate_contracts.py`: PASS, 43 schemas with 43 valid and 43 invalid fixtures.
- `tools/governance/contract_gate.py`: PASS, 88 generated bindings fresh and no competing DTO names detected.
- Ruff check and formatting check: unavailable; `.venv/bin/ruff` does not exist. Import inspection also found mypy unavailable. Neither is a passing quality check.
- Full integration, recovery, security, and release suites were not executed for this planning task. Shared fixtures can provision infrastructure and lifecycle tests can tear it down.

Recheck the working tree and prerequisite evidence before implementation; preserve any concurrent changes. The contract gate was rerun for this update; Ruff and mypy availability were checked through Python module discovery. Findings below come from source inspection, not a completed production qualification. No lint count, coverage percentage, or current DAG-ready task is claimed.

## Findings driving the work

| Priority | Evidence | Consequence |
|---|---|---|
| P0 | `WorkerAdmission.admit_worker` in `quansio/runtime/orchestration.py` calls capability admission inside its transaction; `CapabilityService._admit` in `quansio/control/capability.py` acquires its own pooled connection. | The claimed atomic boundary does not include the capability insert. Reproduce rollback behavior before changing it. |
| P0 | `TenantRepository.get_run` and `update_run_status` filter tenant and run, while `list_runs` also filters workspace. | Workspace authorization is inconsistent at this layer. Verify the intended role policy and calling paths; this is not yet a demonstrated exploit. |
| P1 | `services/quansio_context/main.py` calls its app factory at import; the shared `quansio/platform/service.py:add_health_routes` returns a degraded readiness dictionary without a non-200 status. | Imports require infrastructure, shutdown ownership is unclear, and HTTP readiness can indicate success during dependency failure. |
| P1 | `pyproject.toml` declares lower-bounded dependencies, no lockfile was found, and production artifact code imports undeclared `minio`. The wheel includes only `quansio`. | Fresh installations may differ or omit needed dependencies and generated contracts/deployment resources. |
| P1 | `tools/governance/verify_all.sh` generates authority and ownership artifacts before checking; it does not invoke Ruff or mypy. No checked-in CI workflow was found. | Verification can repair drift before reporting it and does not enforce the stated static-quality tools. |
| P1 | The contract gate detects competing DTO names and freshness; API commands are manually assembled dictionaries, and generated bindings use dictionary payloads. | A passing gate does not prove all runtime boundaries validate canonical contracts or benefit from field-level static typing. |
| P1 | `tests/conftest.py` provisions a shared environment and orders lifecycle tests last. | Test isolation depends on ordering; concurrent or interrupted runs need explicit environment ownership. |
| P2 | `orchestration.py` is 522 lines and `machine_control/services.py` 396; domain APIs frequently expose bare dictionaries and positional database rows. | These are candidates for focused decomposition and stronger interfaces, not justification for a wholesale rewrite. |

| P1 | `clients/web/app.js` keeps one event cursor across followed runs, silently drops sequence gaps, and puts a command ID in the run-ID input. `clients/desktop/package.json` defines only a start script. | Client recovery and command-to-run identity need contract reconciliation; JavaScript quality checks need explicit build integration. |

## Execution rules

Use `registries/tasks.json` and `registries/task-graph.json` as the only task dependency authority. The work packages below are planning labels, not a parallel task registry. At the start of each package, validate prerequisite evidence and select a DAG-ready canonical task. Priority determines attention among eligible work, never permission to skip a milestone gate.

Before adding behavior, record owner service, canonical schema, command, durable store, RuntimeEvent, capability, policy, effect class, idempotency, cancellation, recovery, and qualification. Mark genuinely inapplicable fields with a reason. Use the existing owner and effect paths.

An invariant, ownership, durable-schema, security-boundary, external-effect, or release-transition change needs a decision record using `docs/35_ARCHITECTURE_DECISION_TEMPLATE.md`, including alternatives, risk, migration/rollback, and review trigger. Do not create another orchestrator, policy authority, or durable task store. Refactoring within an owner must preserve its transaction and effect semantics.

## Ordered work packages

### Q1 — Establish a reproducible baseline and blocking checks

Canonical anchors: GOV-001 through GOV-006; ENV-001 for the qualification environment. Owner: existing governance/build maintainers.

1. Record the current working-tree diff, tool versions, dependency versions, and applicable assertion IDs. Measure lint findings, formatting drift, type errors, and test outcomes without rewriting source or evidence.
2. Inventory direct runtime and test imports; declare missing dependencies such as `minio`, choose and check in a dependency lock, and verify an isolated installation.
3. Verify wheel contents and installed imports without repository `sys.path` injection. Include generated contracts and resources through the existing packaging architecture where required.
4. Separate explicit regeneration from read-only verification. Add CI stages following `docs/50_CI_AND_REAL_ENVIRONMENT_BLUEPRINT.md`: authority/integrity, generated bindings, formatting/lint/types, build/install, and applicable tests. Use an existing external CI system if one is authoritative.
5. Enable formatting and focused Ruff correctness/import rules. Introduce strict typing module by module, beginning with platform interfaces and canonical boundaries. Track existing debt explicitly; do not silently ignore failures or use blanket suppression.

Acceptance: a clean checkout installs reproducibly; installed-package smoke checks pass; deliberately stale generated output fails verification without being repaired; a failing lint/type fixture fails its stage; verification leaves tracked inputs unchanged. Existing authority assertions remain blocking.

### Q2 — Prove transaction atomicity and authorization scope

Canonical anchors: DAT-008, SEC-001, RUN-004, RUN-007 and their prerequisites. Owners: existing runtime, control, and tenant repository owners.

1. Add a real-PostgreSQL regression that fails worker admission after child capability insertion and inspects all related rows.
2. Decide how canonical control operations participate in the caller's transaction while retaining control ownership. Pass an explicit transaction/connection through the existing interface where appropriate; avoid ambient global transactions or a second persistence abstraction.
3. Ensure capability, agent, budget, dispatch, and required event/outbox writes use the atomic boundaries specified by their tasks. Audit adjacent nested service calls for the same connection pattern.
4. Resolve workspace-access semantics against the canonical policy. Test a same-tenant user accessing another workspace, a foreign tenant, legitimate scoped access, and any explicitly permitted elevated role. Apply predicates or owner-authorized checks consistently.

Acceptance: failure injection leaves no partial admission state; concurrent admissions cannot exceed budgets; duplicate delivery follows canonical idempotency behavior; revoked/stale authority cannot admit work; crash/restart preserves the defined outcome. Test with real PostgreSQL. Any schema change includes forward migration and recovery/rollback proof.

### Q3 — Make service lifecycle and failure reporting consistent

Canonical anchors: GOV-002, ENV-001, relevant service task, and SRE-001/SRE-002 when DAG-ready. Owners: each registered service; shared platform utilities only for mechanical lifecycle behavior.

1. Replace import-time connection creation with application factories and managed startup/shutdown. Explicitly distinguish owned resources from injected resources.
2. Define dependency-aware readiness per service. Return HTTP 503 on failure, keep liveness separate, and close pools/clients on shutdown and failed startup.
3. Return stable public error codes; put redacted diagnostic details in correlated server logs instead of raw exception strings in responses.
4. Review broad exception handlers individually. Keep broad catches only at justified containment boundaries with explicit failure/recovery behavior.

Acceptance: imports do not connect to infrastructure; dependency outage makes readiness fail; recovery restores readiness; shutdown releases owned resources; failure responses contain no credentials or internal connection details. Exercise real dependency loss for qualification, with unit doubles confined to permitted unit tests.

### Q4 — Strengthen canonical contracts and internal types

Canonical anchors: GOV-003, DAT-005 and relevant command/event tasks. Owners: existing contract generator and consuming service owners.

1. Improve the generator to expose schema-derived field types where practical; preserve runtime schema validation and deterministic generation. Do not hand-edit generated files or duplicate canonical models.
2. Validate at actual command, event, adapter, and persistence boundaries, not merely in fixture checks. Keep transport request types distinct from canonical envelopes.
3. Replace bare dictionaries and positional row plumbing in touched interfaces with schema-derived types or small internal typed records. Correct database context-manager annotations and type ownership of injected resources.
4. Review `/v9/commands` admission semantics: it currently returns an envelope without persisting or dispatching it in that handler. Reconcile this against the canonical command task before claiming durable acceptance; implement any missing behavior only through its existing owner.

Acceptance: malformed, unknown-field, stale-revision, and invalid enum payloads fail at the intended boundary; valid payloads round-trip without digest changes; generator freshness and strict typing pass for migrated modules. Durable command claims require replay/idempotency proof, not response-shape tests alone.

### Q5 — Isolate tests and make recovery evidence repeatable

Canonical anchors: GOV-006, ENV-001, DAT-002 and the applicable qualification tasks. Owners: qualification tooling and relevant service owners.

1. Separate unit/contract, durable integration, lifecycle, and external qualification invocations with explicit markers and environment preflight.
2. Give each integration job isolated databases/namespaces and credentials. Keep teardown tests on their own stack so ordering cannot affect other suites.
3. Add targeted races, duplicate delivery, cancellation, partial failure, and restart tests around the Q2–Q4 changes. Cover migration forward application and the required rollback/recovery strategy.
4. Record coverage as a diagnostic baseline. Require changed critical branches to be exercised; prioritize exact canonical assertion coverage over an arbitrary repository-wide percentage.

Acceptance: isolated suites run in different orders without shared-state failures; lifecycle teardown cannot damage another job; required unavailable external boundaries report `BLOCKED_REAL_BOUNDARY`; unexplained flaky failures remain failures. Reports include exact assertion IDs, environment identity, reachable commit, actual artifact digests, and required recovery evidence.

### Q6 — Refactor high-cost domain code incrementally

Canonical anchors: relevant RUN, MAC, MOD, EFF, CTX, and other domain tasks after prerequisite reconciliation. Owner: each existing domain service.

Start with worker admission/budgets, then machine lifecycle and model/effect boundaries according to measured change frequency and defects. Extract coherent operations inside the same owner, name state transitions explicitly, centralize repeated row conversion and error mapping, and remove dead imports/branches proven unused. Preserve transaction scope, event ordering, cancellation, and canonical effect routing.

Acceptance: behavior-preserving refactors pass existing positive, adversarial, and recovery assertions; no second execution path appears; public contracts and digests remain compatible. Measure complexity and duplication before/after as supporting evidence. Do not split files solely to reach a line-count target.

### Q7 — Verify client projections and JavaScript quality

Canonical anchors: UX-001 and UX-006 with their actual prerequisites. Owner: existing client projection layer; runtime retains event and run authority.

1. Resolve command-to-run identity using the canonical command response and runtime APIs. Remove the command-ID-as-run-ID shortcut only after the server exposes the required authoritative mapping.
2. Reconcile event sequence scope with the runtime contract. Scope cursors to the defined stream, reset projection state when switching identity/workspace, and recover gaps through canonical replay or snapshots. Do not invent missing state locally.
3. Add JavaScript linting, formatting, a dependency lock, and installed Electron startup validation to Q1 build checks. Keep the existing Electron isolation settings enforced.
4. Exercise switching between two runs, duplicate and missing events, reconnect, expired sessions, malformed stored identity, and command failure. Use real server boundaries for qualification and permitted unit doubles only for isolated rendering tests.

Acceptance: following one run cannot suppress another run's events; gaps trigger observable recovery; commands resolve to server-issued run identities; logout/workspace changes clear prior projections; client validation runs in CI alongside Python checks.

## Reviewable delivery order and measurements

These dependencies order improvement work only; canonical DAG eligibility still controls execution. Q1 enables measurement and tooling. Q2 correctness reproducers can proceed alongside Q1 when eligible. Q3 and Q4 use that baseline; Q5 isolation should land before running their destructive recovery suites. Q6 follows regression coverage for each touched operation. Q7 identity work depends on Q4's server contract reconciliation.

| Pull-request scope | Required evidence before merge |
|---|---|
| Baseline report and read-only verification separation | Exact commands, versions, failures, and clean-tree check; stale output must fail rather than regenerate. |
| Dependency lock and installed-package checks | Fresh install, wheel/resource inventory, service import checks, client build/startup checks. |
| Worker admission atomicity | Failing real-database reproducer before the fix, passing rollback/race/idempotency cases afterward, decision record. |
| Workspace authorization consistency | Policy decision, same-tenant cross-workspace and foreign-tenant tests, legitimate access retained. |
| Shared readiness and resource lifecycle | HTTP 503 under outage, recovery to ready, deterministic shutdown, redacted diagnostics. |
| One contract boundary at a time | Generated types, runtime rejection cases, strict type check, replay evidence where durable admission changes. |
| Test environment isolation and client recovery | Job ownership and teardown proof; run switching, event gaps, reconnect, and authoritative identity tests. |

Q1 should record counts of lint/type violations by module, formatting drift, installed-import failures, test duration and flaky failures, and critical assertion coverage. Subsequent changes must introduce no new findings under enabled blocking rules. Existing debt needs explicit tracked scope and removal criteria; do not convert failing release assertions into accepted debt. Report transaction residue, unauthorized access, false-ready responses, and unrecovered client gaps as behavioral failures rather than folding them into a cosmetic quality score.

## Delivery and completion

Begin with Q1 baseline/verification separation and a Q2 atomicity reproducer once its prerequisites are verified. Keep formatting-only edits separate from behavioral fixes. Each later pull request should address one reviewable invariant or interface and include relevant validation and rollback notes.

For every package: READ → task-specific reconciliation → PLAN → IMPLEMENT → MIGRATE → positive tests → adversarial tests → recovery tests → security/observability verification → evidence → validation → next DAG-ready task.

Completion requires functioning CI quality gates, reproducible installation and packaging, proven corrected transaction/readiness behavior, typed and validated touched boundaries, isolated qualification runs, and reproducible canonical evidence. This plan itself does not qualify the product or establish production readiness. Effort estimates should follow Q1 measurements and prerequisite validation.
