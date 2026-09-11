# Quansio V9 Final Master Dossier

**Schema revision:** `9.0.0`

This is the consolidated reading copy. Canonical registries and schemas remain machine-readable authority.


---

<!-- source: 00_README.md -->

# Quansio V9 Final Implementation Authority

**Schema revision:** `9.0.0`

This directory is the complete implementation authority for Quansio. It is intended for direct use by implementation agents and human engineers. The authority is self-contained: architecture, product behavior, service ownership, canonical contracts, machine-readable requirements/tasks, dependency graph, wiring, support matrix, qualification, release gates, source-completeness checks and evidence validation are all included.

## Product contract

Quansio is one governed platform combining:

1. **Persistent autonomous work** — durable digital teammates, ephemeral workers, collaboration, routines, browser/computer execution, connectors, approvals and multi-device continuation.
2. **Evidence-first intelligence** — typed programmable research, wide/deep discovery, entity resolution, verification, provenance, freshness and reproducible scoring.
3. **Quansio for Business** — Business Capability Packs and a Capability Compiler that turn authoritative enterprise material into governed, evaluated executable capabilities.
4. **Controlled Skill Evolution** — evidence-backed candidate skill extraction, isolated evaluation, governed promotion, versioning and rollback.

All four outcomes execute through the same canonical runtime, policy, tool, effect, evidence, knowledge, machine and recovery primitives.

## Start here

Read `AGENTS.md`, `HANDOFF.md`, the master dossier, `docs/19_IMPLEMENTATION_PLAN.md`, `docs/20_ATOMIC_TASK_REGISTRY.md`, `docs/21_WIRING.md`, `docs/26_REAL_IMPLEMENTATION_COMPLETION_CONTRACT.md`, `docs/27_TEST_VERIFICATION_AND_EVIDENCE.md`, all canonical schemas/registries and the implementation kickoff prompt.

Run:

```sh
python3 scripts/validate_authority.py
python3 scripts/validate_contracts.py
python3 scripts/self_test_validators.py
```

Counts are generated from canonical registries: **135 tasks, 111 requirements, 43 canonical schemas**.


---

<!-- source: AGENTS.md -->

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


---

<!-- source: HANDOFF.md -->

# Implementation handoff

Use this package as the sole active implementation authority. Implementation begins at the earliest DAG-ready task whose dependencies have valid evidence. Do not restart completed work merely to gain familiarity; re-open a task only when its governed inputs materially changed or its evidence fails current validation.

The target is a production platform, not a prototype. Every feature must be wired end-to-end through canonical owners, real durable boundaries and the defined qualification suites.

The master dossier is a reading view. Machine-readable truth for tasks, requirements, dependencies, schemas, support and release state lives under `registries/` and `schemas/`. Generated reading views must match those sources exactly.


---

<!-- source: INSTALL.md -->

# Install authority

Place the complete `Quansio_V9_FINAL_IMPLEMENTATION_AUTHORITY` directory at the repository's canonical active-authority location. Ensure no other authority package is included in active agent search, generation or validation scope. Do not delete application source or production data as part of authority installation.

After placement, run all authority validators and record the output. The authority directory must remain immutable during an implementation task except through deliberate specification-maintenance work; task implementation belongs in application source, migrations, tests and deployment code.


---

<!-- source: SKILLS.md -->

# Skills — Controlled Skill Evolution

A skill is procedural know-how for one class of task. It is not an agent runtime, permission source, connector owner or recovery mechanism.

Pipeline:

`authoritative material → candidate extraction → semantic decomposition → procedural reconstruction → candidate SkillPackage → static/security checks → isolated evaluation → regression evaluation → governed promotion → versioned registry → task-scoped materialization`

A candidate cannot self-promote, broaden capabilities, bypass evaluation or introduce an alternate execution path. Promotion and rollback are registry/control-plane operations. Runtime receives only qualified versions admitted by Capability Projection.


---

<!-- source: TOOLS.md -->

# Tools — Canonical Tool Registry

Every executable tool operation has one versioned contract containing input/output schema, semantic effect class, fidelity, required capability, policy requirements, timeout, idempotency and evidence expectations.

Fidelity classes: `LOSSLESS`, `LOSSLESS_WITH_CONSTRAINTS`, `BEST_EFFORT_DEGRADING`, `IRREVERSIBLE`, `HUMAN_ONLY`, `UNSUPPORTED`.

Effect classes: `OBSERVATIONAL`, `NON_CONSEQUENTIAL`, `CONSEQUENTIAL`, `HIGH_RISK`, `SEMANTICALLY_CLASSIFIED`.

A low-level browser/computer action never bypasses semantic classification. If its real outcome sends, publishes, purchases, deletes, modifies protected state or uploads protected information, it enters the canonical consequential-effect path before actuation.


---

<!-- source: docs/01_PRODUCT_CONTRACT.md -->

# 01 — Product contract

Quansio is a persistent autonomous work platform with evidence-first intelligence and governed business capabilities. A user can create durable teammates, delegate parallel work, research broadly and deeply, operate managed computers/browsers, use enterprise connectors, schedule routines, approve protected actions, inspect evidence and resume work from any supported client.

## Product outcomes

### Persistent autonomous work
- Persistent teammate identity is distinct from conversation, WorkGraph, workspace, machine and client session.
- Ephemeral workers are admitted transactionally and cannot outlive or exceed admitted authority/budget.
- Parallel work is asynchronous, durable and incrementally observable.
- Client termination does not terminate eligible server-side work.
- Approvals, waits, notifications and routines are durable.

### Evidence-first intelligence
- Research is expressed as typed bounded `SearchProgram` operations, not arbitrary generated executable code.
- Retrieval, entity resolution, ranking, extraction, verification and synthesis preserve source/evidence identities.
- Wide/deep research exposes missing, stale, conflicting and inaccessible evidence explicitly.
- Research quality is measured by reproducible benchmark formulas and thresholds.

### Quansio for Business
- Business Capability Packs compose knowledge, skills, tools/connectors, policies, RBAC, approvals, workflows, I/O contracts, evidence, evaluations and compatibility.
- Capability Compiler is an authoring pipeline. Runtime execution still uses canonical WorkGraph, tools, policy/effects, evidence and recovery.

### Controlled Skill Evolution
- Skill candidates are derived from authoritative material, evaluated in isolation and promoted only by governance rules.
- A skill never becomes a source of authority and never introduces another runtime.


---

<!-- source: docs/02_ARCHITECTURAL_INVARIANTS.md -->

# 02 — Architectural invariants

1. **One runtime authority.** WorkGraph/AgentGraph/StateGraph plus GraphTransaction own task execution state.
2. **Model proposes; runtime owns reality.** Model output can propose tools/plans/content but cannot directly mutate authoritative state or external systems.
3. **One effect path.** Consequential actions require semantic operation, capability, policy/privacy/security, approval where needed, EffectRecord, actuation, receipt/evidence and reconciliation.
4. **Memory is not recovery.** Canonical events, protocol state, checkpoints, execution generations and effect reconciliation restore execution.
5. **Clients are projections.** Desktop/web/mobile/CLI cannot become task/effect/approval/model authority.
6. **Server-side model fulfillment.** Provider credentials and provider calls live only in the model gateway trust boundary.
7. **One Knowledge Fabric.** Enterprise/user/research/successful-work/engineering knowledge share one semantic store/query model with provenance; protocol and recovery state remain separate.
8. **One Tool Registry.** Research, business, automation and general work resolve the same typed operations.
9. **Authority narrows.** Child capabilities, budgets, target scope and credentials are strict subsets of admitted parent authority.
10. **No superficial completion.** Interfaces/UI/tests without real production wiring do not satisfy acceptance.


---

<!-- source: docs/03_SYSTEM_ARCHITECTURE.md -->

# 03 — End-to-end system architecture

```text
Clients
Desktop | Web | Mobile | CLI | Admin
             |
             v
        quansio-api
             |
       quansio-control
             |
        quansio-runtime
   /          |           \
  v           v            v
Context    Model Gateway   Effect Path
  |           |            |
Indexer    Model Profiles  Integration Broker
  |                        |
Artifact <-----------------+
  ^                        |
  |                        v
Worker Gateway ------> Machine Control
                           |
                           v
                         qworkerd
                  isolated/persistent/private targets

Control/Runtime ------> quansio-notify
All owners -----------> canonical events/telemetry/evidence
```

## Canonical owners

| Owner | Owns | Must not own |
|---|---|---|
| `quansio-api` | Authenticated public commands, session entry, event projection, upload initiation. | No graph execution, provider credential custody, effect settlement, or machine actuation. |
| `quansio-control` | Tenant/identity/RBAC/policy/approval/registry/schedule/support configuration authority. | No model, browser, connector, or guest actuation. |
| `quansio-runtime` | Canonical WorkGraph/AgentGraph/StateGraph execution, admission, turns, waits, cancellation, budgets, recovery coordination. | No direct provider credentials or unmediated external effects. |
| `quansio-model-gateway` | All model fulfillment, provider adapters, routing, streaming, usage settlement, model egress policy. | No task truth, user approval truth, or general connector authority. |
| `quansio-context` | Context Projection, SearchProgram execution, retrieval coordination, evidence assembly, Knowledge Fabric queries. | No independent task scheduler or effect path. |
| `quansio-indexer` | Ingestion, chunking, indexing, freshness, tombstones and index provenance. | No model orchestration or business workflow authority. |
| `quansio-worker-gateway` | Authenticated worker/guest transport, lease/generation validation, ACK/redelivery and cancellation relay. | No tenant policy ownership or model credentials. |
| `quansio-machine-control` | Execution-target inventory, placement, leases, generations, snapshots, restore and migration. | No application task truth or provider fulfillment. |
| `quansio-integration-broker` | Connector adapters, credential handles, typed external operations and webhook ingress. | No policy/effect bypass; no ambient tenant secret exposure. |
| `quansio-artifact` | Immutable artifacts/evidence, digests, scanning, grants and lifecycle. | No task orchestration. |
| `quansio-notify` | Durable attention/notification delivery and receipt tracking. | No approval truth or task state authority. |
| `qworkerd` | Guest actuator for assigned filesystem/terminal/browser/computer/process operations. | No ambient cloud authority, provider credentials, or tenant policy ownership. |

Logical services may share a deployable during early implementation only when ownership, schema and interfaces remain explicit and tests prove no hidden alternate authority. Scaling or extraction must not change semantics.

## Trust boundaries
- Interactive clients: untrusted for canonical identity fields; authenticate and receive scoped server authority.
- Public API/control: validates identity/tenant/policy commands; does not execute provider/tool/machine actions directly.
- Runtime: authoritative orchestration and state transition boundary.
- Model gateway: provider credential and provider protocol boundary.
- Integration broker: connector credential handle and external operation boundary.
- Worker/machine fabric: task-scoped execution boundary with generation/lease/fence.
- Artifact/evidence: immutable content/digest boundary.


---

<!-- source: docs/04_FRONTEND_DESIGN.md -->

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


---

<!-- source: docs/05_BACKEND_AND_CONTROL_PLANE.md -->

# 05 — Backend and control plane

## API
Public commands authenticate first, resolve server-owned tenant/user/workspace/session identity, validate schema/revision/idempotency and dispatch to canonical owner. APIs do not accept client assertions of completed task/effect/approval truth.

## Control plane
Owns tenant configuration, users/roles, policies, approvals, skill/business/tool registries, automation definitions, support selection and administrative configuration. Runtime consumes versioned snapshots/decisions rather than reading mutable client configuration directly mid-step.

## Runtime
Owns graph execution, waits, worker lifecycle, cancellation, budget reservation, model/tool requests and recovery coordination. Every durable transition produces canonical event/protocol state through transaction boundaries.

## Integration broker
Owns connectors and webhooks. Credentials are brokered as scoped handles. Consequential operations require EffectRecord; adapters cannot invoke external state changes from an unmediated helper path.

## Artifact service
Stores immutable content/evidence by digest, scan state, tenant, provenance and grants. Artifacts can be referenced by tasks/research/effects without embedding large bytes in canonical event payloads.


---

<!-- source: docs/06_DATA_EVENTS_AND_RECOVERY_STATE.md -->

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


---

<!-- source: docs/07_RUNTIME_AGENTS_AND_COLLABORATION.md -->

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


---

<!-- source: docs/08_SERVER_MODEL_FULFILLMENT.md -->

# 08 — Server-side model fulfillment

All provider communication flows through `quansio-model-gateway`.

## Admission path
`runtime step → capability/context/budget/privacy constraints → deterministic route decision → ModelRequestEnvelope → provider adapter → ModelEvent stream → runtime`

No mandatory model call may exist solely to choose another model.

## Streaming contract
`MODEL_STARTED` occurs once before deltas. Valid intermediate events: `OUTPUT_DELTA`, `TOOL_PROPOSAL`, `USAGE_DELTA`. Exactly one terminal event: `MODEL_COMPLETED`, `MODEL_CANCELLED`, `MODEL_FAILED`. Sequences are monotonic; post-terminal events are invalid.

## Usage/budget
Reserve budget before provider start. Streaming/final usage settles against the same reservation. Cancellation does not immediately free uncertain usage: state can remain `SETTLING_PROVIDER_USAGE` until final provider usage arrives. Duplicate late usage is idempotent; corrections are append-only adjustments.

## Privacy/residency
Classify context before provider egress. The gateway enforces destination/residency/policy and must prove zero protected bytes leave on denial. Provider adapters do not synthesize absent policy/budget/provenance fields.

## Qualification
An enabled model profile must exercise a real request, stream, cancellation, usage, malformed response and outage/failover behavior using exact deployed adapter/configuration artifacts.


---

<!-- source: docs/09_CONTEXT_RESEARCH_AND_EVIDENCE.md -->

# 09 — Context, research and evidence-first intelligence

## SearchProgram
Allowed operators are `SEARCH`, `RETRIEVE`, `FAN_OUT`, `FILTER`, `RANK`, `DEDUPLICATE`, `JOIN`, `EXTRACT`, `RESOLVE_ENTITY`, `VERIFY`, `ITERATE`, `SYNTHESIZE`. Operator inputs/outputs are typed references. Fan-out <=1000; iteration <=20 unless a future schema revision explicitly changes the bound.

Filter/stop predicates are data ASTs using `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `contains`, `in`, `exists`, `and`, `or`, `not`. Executable predicate/code strings are invalid.

## Research record
Separate canonical entity identity, attributes, claims, source refs, freshness, confidence and verification. A citation existing is not proof; verification can independently refetch the source and classify supported/unsupported/stale/inaccessible/conflicting.

## Wide/deep execution
Parallel discovery/enrichment uses durable intermediate result sets, deduplication and explicit cost/time/fan-out limits. Partial results identify missing/error states rather than fabricating completion.

## Blocking quality thresholds
- discovery recall >= 0.90
- entity precision >= 0.95
- claim/attribute precision >= 0.95
- citation support >= 0.98
- freshness compliance >= 0.98
- duplicate rate <= 0.02
- hard completion >= 0.85

The benchmark binds dataset digest, source-policy identity, scorer revision and metric formulas so results are reproducible.


---

<!-- source: docs/10_KNOWLEDGE_AND_CONTROLLED_SKILLS.md -->

# 10 — Knowledge Fabric and Controlled Skill Evolution

Knowledge candidates carry provenance, evidence, source epoch, confidence, validity and conflicts. Asynchronous synthesis commits only if relevant source/task epochs still match; stale results are rejected but retained diagnostically.

Knowledge Fabric stores semantic knowledge. It does not store the authoritative live run protocol and cannot be used to reconstruct missing execution state.

## Skill lifecycle
`authoritative material → candidate → static/security checks → isolated evaluation → regression → qualified version → registry → task-scoped materialization`

Promotion is a separate governed control-plane operation. Skill helpers cannot mutate promotion, policy or capability authority. Running tasks remain pinned to their admitted skill version; rollback changes resolution for new work.


---

<!-- source: docs/11_BUSINESS_CAPABILITY_PACKS.md -->

# 11 — Quansio for Business: Business Capability Packs

A Business Capability Pack is a deployable, versioned, evaluated enterprise capability. It is intentionally broader than a skill.

Required composition:
- authoritative knowledge requirements
- qualified skills
- typed tool and connector requirements
- role and permission requirements
- credential-handle requirements
- policies and approval rules
- WorkGraph/workflow templates
- input/output contracts
- evidence requirements
- evaluation cases and mandatory thresholds
- compatibility, migration, deprecation and rollback policy

## Capability Compiler

```text
Authoritative docs / SOPs / policies / APIs / process definitions
Permissions / schemas / successful-work evidence
                  |
                  v
        semantic decomposition
        process reconstruction
        candidate skill resolution
        tool/connector binding
        RBAC + policy + approval binding
        workflow compilation
        evaluation generation
        compatibility analysis
                  |
                  v
          Candidate Capability Pack
                  |
             qualification
                  |
                  v
          Published Capability Pack
```

The compiler does not execute production work. Published packs resolve into canonical WorkGraph, SkillPackage, ToolOperation, CapabilitySnapshot, PolicyDecision, approvals, effects and evidence at runtime.


---

<!-- source: docs/12_TOOLS_APPROVALS_AND_EFFECTS.md -->

# 12 — Tools, approvals and external effects

## Tool fidelity
A tool can be technically callable while unsuitable for a business capability. Fidelity is explicit: lossless, constrained-lossless, degrading, irreversible, human-only or unsupported.

## Consequential path

```text
Tool proposal / semantic action
          |
          v
CapabilitySnapshot
          |
PolicyDecision + privacy + sequence guard
          |
ApprovalRequest if required
          |
EffectRecord
          |
Actuator / Integration Broker / Browser / Machine
          |
Receipt + evidence
          |
Settlement / reconciliation
```

Effect states: `PROPOSED`, `APPROVAL_REQUIRED`, `APPROVED`, `EXECUTING`, `UNKNOWN`, `COMMITTED`, `DENIED`, `FAILED`, `RECONCILED`.

## Exact-scope approvals
Approval binds semantic operation/effect/normalized argument digest/target/risk/expiry. Financial scope additionally binds payee, amount in minor units, currency, purpose, funding handle, per-effect ceiling and cumulative budget. Changing amount by one minor unit or changing payee invalidates the receipt.

## UNKNOWN
After an ambiguous timeout the system must not retry blindly. It queries provider/target state using original idempotency/effect identity, records reconciliation, and only retries if that evidence proves no effect occurred and the operation is safe to retry.


---

<!-- source: docs/13_SECURITY_PRIVACY_AND_AUTHORITY.md -->

# 13 — Security, privacy and authority

## Security chain
`authenticated actor → CapabilitySnapshot → PolicyDecision → privacy classification → sequence guard → scoped credential handle → approval/effect as required → actuator`

### Capability
Snapshot is immutable for an admitted step and carries explicit atoms/constraints/expiry/parent. Child snapshots are strict subsets.

### Policy
Decision binds actor, capability, operation, normalized arguments, target, data class and policy revision. Argument change requires a new decision.

### Privacy
Before remote model/connector/upload/worker egress, classify sensitive data and apply destination-aware allow/redact/approval/deny. A denied path sends zero protected bytes.

### Credentials
Secret material remains behind brokered handles. Handles are short-lived and operation/target/tenant scoped. Guests and clients cannot request reusable plaintext credential material.

### Sequence guard
Rules can identify dangerous combinations across canonical events/effects. A later operation may be denied/escalated based on earlier authorized activity.

### Tenant isolation
Enforce at API, repository, event stream, object/evidence, context, model, connector, worker, machine and client cursor boundaries. Fail closed when authoritative security state is unavailable.


---

<!-- source: docs/14_QUANSIO_BOX_MACHINE_ARCHITECTURE.md -->

# 14 — Quansio Box execution architecture

## Target classes
- Hosted isolated task runtime
- Persistent workspace computer
- Local virtualized target when qualified
- Private worker target when qualified
- Personal endpoint relay

## Quansio Box
A hosted target is a tenant-bound microVM-class environment containing `qworkerd`, workspace mounts/artifact inputs, managed browser where required and deny-by-default networking. Credentials remain outside the guest where practical; scoped handles or mediated network/session injection are preferred.

```text
Runtime
  |
Worker Gateway -- authenticated envelope / ACK / cancellation
  |
Machine Control -- target / lease / generation / fence / snapshot
  |
Quansio Box
  |- qworkerd typed RPC
  |- filesystem / terminal / process
  |- managed browser / computer
  |- policy-controlled egress
  `- task-scoped capabilities only
```

## Lifecycle
`PROVISIONING → READY → LEASED → HIBERNATED/MIGRATING/UNHEALTHY → READY or TERMINATED`.

Placement must hold an exclusive lease and fence. Restore/migration invalidates stale actors through generation/fence changes.

## Checkpoints
Workspace snapshots occur more frequently than full-machine checkpoints. `RESTORABLE` is assigned only after every referenced state/artifact/snapshot object is durable and digest-verified. Warm pools and copy-on-write optimization are performance work after isolation/recovery correctness passes.


---

<!-- source: docs/15_BROWSER_COMPUTER_AND_ENDPOINT.md -->

# 15 — Browser, computer and personal endpoint control

One canonical browser/computer stack serves research, general work, automation and business capabilities.

## Browser control preference
Prefer structured page/accessibility/network/session state for deterministic actions and extraction. Visual interpretation is a fallback for content/control not adequately represented structurally.

## Live session
The same browser session is shown to the user. Viewer/controller identity is explicit. Human takeover obtains controller authority; return of control requires the agent to re-observe current state before continuing.

## Semantic browser effects
`click`, `type`, `select`, `submit` are actuator primitives, not effect classes. Semantic outcome is determined before consequential actuation. Purchases, sends, publications, destructive writes and protected uploads require the normal policy/approval/effect path.

## Endpoint relay
`EndpointActionEnvelope` binds endpoint/target, execution generation, lease, fence, capability, policy, effect, delivery attempt, idempotency, operation/schema revision, expiry and approval receipt/scope when required. Stale generation/fence, expired action or mismatched approval scope is rejected before endpoint actuation. ACK/redelivery returns the original result for a completed idempotency identity.


---

<!-- source: docs/16_AUTOMATION_COLLABORATION_AND_ATTENTION.md -->

# 16 — Automations, collaboration and attention

## Automations
Schedules include timezone, local rule, DST gap/fold policy, missed-fire policy and logical fire identity. `CATCH_UP_BOUNDED` has explicit maximum. Every fire resolves current agent/capability/policy/support/target state; schedule creation does not freeze authority.

Pause/resume/delete serialize against scheduler claim. Scheduler restart uses durable fire history to prevent duplicate logical work.

## Collaboration
Collaboration is a projection over agents, messages, handoffs and WorkGraph turns. It does not own a second work scheduler. Typed handoffs carry sender/recipient, target work/turn, payload/artifact refs, capability context and delivery identity.

## Notifications
Notifications carry recipient, attention type, urgency, expiry/deep-link and delivery/ack state. Notification delivery never becomes approval truth; approval lives in the control/effect contract.


---

<!-- source: docs/17_API_AND_PROTOCOL_CONTRACTS.md -->

# 17 — API and protocol contracts

All canonical wire/durable contracts carry `schema_revision: "9.0.0"` and reject missing/unknown revisions unless a deliberately implemented compatibility adapter validates all required authority fields from trusted state.

## Command rules
- Server resolves authenticated actor/tenant/workspace identity.
- Client supplies command-specific arguments and idempotency identity, not canonical completion/effect truth.
- Commands return accepted/rejected plus stable command/run identifiers; long work is observed through events.

## Versioning
Breaking contract change creates a new schema revision, fixtures, generated bindings, compatibility decision and migration tests. Never accept an older incomplete envelope by inventing approval, capability, policy, budget, generation, tenant or provenance fields.

## Fixtures
Each critical contract family has valid fixtures plus invalid fixtures for omitted required identity/policy/generation/scope fields. Contract CI validates fixtures against the exact registered schema.


---

<!-- source: docs/18_OBSERVABILITY_SRE_AND_DR.md -->

# 18 — Observability, SRE and disaster recovery

## Correlation
Logs/metrics/traces correlate command, session, run, step, model request, tool operation, effect, worker, target and recovery point. Protected payload content is not emitted merely to improve observability.

## Objectives
- Authenticated command/event API availability: 99.95% monthly.
- Command admission p95: <=500 ms, excluding external provider/tool latency.
- Event projection lag p95: <=2 s under qualified load.
- Warm isolated runtime readiness p95: <=20 s; cold p95: <=60 s for the qualified hosted profile.
- Authoritative state: RPO <=300 s, RTO <=1800 s.
- Evidence/object state: RPO <=900 s, RTO <=3600 s.

## DR
Backups alone are not proof. Restore drills bind RecoveryConsistencyPoint and validate database/events/evidence/snapshots/effects together. Unresolved UNKNOWN effects are reconciled before consequential work reopens.

## Load/degradation
Admission, queueing, fan-out, model usage, worker placement, storage and connector budgets are bounded. Dependency overload triggers explicit backpressure/degradation rather than uncontrolled retry loops or cross-tenant resource theft.


---

<!-- source: docs/19_IMPLEMENTATION_PLAN.md -->

# 19 — Implementation plan

The machine-readable task DAG is canonical. This view is generated from it.

## Milestone M0
**Tasks:** 9

- `GOV-001` — Adopt repository into canonical ownership — deps: none
- `GOV-002` — Freeze canonical service and state ownership — deps: GOV-001
- `GOV-003` — Install canonical schema and generated-binding gate — deps: GOV-001, GOV-002
- `GOV-004` — Make authority generation deterministic — deps: GOV-002, GOV-003
- `GOV-005` — Enforce production-source completeness scan — deps: GOV-003
- `GOV-006` — Enforce reproducible completion evidence — deps: GOV-003, GOV-004, GOV-005
- `GOV-007` — Establish architecture-decision and threat-model workflow — deps: GOV-002
- `ENV-001` — Provision implementation qualification environment — deps: GOV-006, GOV-007
- `GATE-M0` — Milestone acceptance gate — deps: ENV-001, GOV-001, GOV-002, GOV-003, GOV-004, GOV-005, GOV-006, GOV-007

## Milestone M1
**Tasks:** 10

- `DAT-001` — Implement tenant and authenticated session authority — deps: GATE-M0
- `DAT-002` — Create authoritative relational schema and migrations — deps: GATE-M0
- `DAT-003` — Implement canonical RuntimeEvent append and replay — deps: DAT-002
- `DAT-004` — Implement transactional outbox delivery — deps: DAT-003
- `DAT-005` — Persist resumable protocol state — deps: DAT-002, DAT-003
- `DAT-006` — Implement immutable artifact and evidence storage — deps: DAT-002, ENV-001
- `DAT-007` — Constrain cache and lease store to non-authoritative use — deps: DAT-002, DAT-005
- `DAT-008` — Enforce tenant-safe repository/query layer — deps: DAT-002, DAT-001
- `SEC-001` — Implement foundational immutable CapabilitySnapshot — deps: DAT-001, DAT-005
- `GATE-M1` — Milestone acceptance gate — deps: DAT-001, DAT-002, DAT-003, DAT-004, DAT-005, DAT-006, DAT-007, DAT-008, SEC-001, GATE-M0

## Milestone M2
**Tasks:** 9

- `RUN-001` — Implement canonical WorkGraph persistence — deps: GATE-M1
- `RUN-002` — Implement AgentGraph lifecycle — deps: RUN-001, SEC-001
- `RUN-003` — Implement StateGraph and GraphTransaction — deps: RUN-001, DAT-003
- `RUN-004` — Implement transactional worker admission — deps: RUN-002, RUN-003, SEC-001
- `RUN-005` — Implement asynchronous fan-out and fan-in — deps: RUN-004
- `RUN-006` — Implement effect-aware cancellation — deps: RUN-005
- `RUN-007` — Implement atomic hierarchical budget reservation — deps: RUN-004
- `RUN-008` — Implement durable waits and callbacks — deps: RUN-003, DAT-005
- `GATE-M2` — Milestone acceptance gate — deps: RUN-001, RUN-002, RUN-003, RUN-004, RUN-005, RUN-006, RUN-007, RUN-008, GATE-M1

## Milestone M3
**Tasks:** 9

- `MOD-001` — Establish model gateway as exclusive fulfillment boundary — deps: GATE-M2
- `MOD-002` — Implement provider-neutral adapter contract — deps: MOD-001
- `MOD-003` — Implement deterministic capability-demand routing — deps: MOD-001, RUN-007
- `MOD-004` — Implement canonical streaming, cancellation and backpressure — deps: MOD-002, MOD-003
- `MOD-005` — Implement usage reservation and late settlement — deps: MOD-004, RUN-007
- `MOD-006` — Implement model privacy and residency enforcement — deps: MOD-001, DAT-001
- `MOD-007` — Implement provider failure isolation and failover — deps: MOD-004, MOD-005
- `MOD-008` — Qualify enabled model profile at real boundary — deps: MOD-005, MOD-006, MOD-007
- `GATE-M3` — Milestone acceptance gate — deps: MOD-001, MOD-002, MOD-003, MOD-004, MOD-005, MOD-006, MOD-007, MOD-008, GATE-M2

## Milestone M4
**Tasks:** 9

- `CTX-001` — Implement typed bounded SearchProgram — deps: GATE-M3
- `CTX-002` — Implement retrieval adapters and source provenance — deps: CTX-001
- `CTX-003` — Implement ResearchRecord and entity resolution — deps: CTX-002
- `CTX-004` — Implement wide and deep research execution — deps: CTX-001, CTX-003
- `CTX-005` — Implement independent claim and source verification — deps: CTX-002, CTX-003
- `CTX-006` — Implement bounded Context Projection — deps: CTX-005, DAT-005
- `CTX-007` — Implement index freshness and tombstone semantics — deps: CTX-002, DAT-006
- `CTX-008` — Qualify reproducible research scoring — deps: CTX-004, CTX-005, CTX-007
- `GATE-M4` — Milestone acceptance gate — deps: CTX-001, CTX-002, CTX-003, CTX-004, CTX-005, CTX-006, CTX-007, CTX-008, GATE-M3

## Milestone M5
**Tasks:** 8

- `SEC-002` — Implement argument-bound policy decisions — deps: SEC-001
- `SEC-003` — Implement destination-aware privacy gate — deps: SEC-002
- `SEC-004` — Implement scoped credential broker — deps: SEC-002, DAT-001
- `SEC-005` — Implement behavior-sequence guard — deps: SEC-002, SEC-003
- `EFF-001` — Implement universal Effect Ledger — deps: SEC-002, SEC-005
- `EFF-002` — Implement durable scoped approvals — deps: EFF-001
- `EFF-003` — Implement UNKNOWN effect reconciliation — deps: EFF-001, EFF-002
- `GATE-M5` — Milestone acceptance gate — deps: EFF-001, EFF-002, EFF-003, SEC-002, SEC-003, SEC-004, SEC-005, GATE-M4

## Milestone M6
**Tasks:** 9

- `MAC-001` — Implement execution-target inventory and lifecycle — deps: GATE-M5
- `MAC-002` — Implement exclusive placement, lease and fence — deps: MAC-001
- `MAC-003` — Implement qworkerd typed guest protocol — deps: MAC-002, SEC-004
- `MAC-004` — Implement durable worker delivery, ACK and redelivery — deps: MAC-003
- `MAC-005` — Implement isolated task runtime — deps: MAC-003, SEC-003
- `MAC-006` — Implement persistent workspace computer — deps: MAC-002, DAT-006
- `MAC-007` — Implement checkpoint, snapshot, restore and migration — deps: MAC-005, MAC-006, DAT-006
- `MAC-008` — Implement private execution target path — deps: MAC-004, MAC-007
- `GATE-M6` — Milestone acceptance gate — deps: MAC-001, MAC-002, MAC-003, MAC-004, MAC-005, MAC-006, MAC-007, MAC-008, GATE-M5

## Milestone M7
**Tasks:** 9

- `BRW-001` — Provision managed browser session architecture — deps: GATE-M6
- `BRW-002` — Implement structured browser actions and observation — deps: BRW-001
- `BRW-003` — Enforce semantic effect classification for browser actions — deps: BRW-002, EFF-001, EFF-002
- `BRW-004` — Implement human observation and takeover — deps: BRW-001, MAC-002
- `BRW-005` — Implement governed browser file transfer — deps: BRW-002, DAT-006
- `BRW-006` — Implement personal endpoint relay — deps: MAC-004, EFF-001
- `BRW-007` — Persist browser/computer observation evidence — deps: BRW-002, DAT-006
- `BRW-008` — Qualify enabled browser and endpoint profiles — deps: BRW-003, BRW-004, BRW-005, BRW-006, BRW-007
- `GATE-M7` — Milestone acceptance gate — deps: BRW-001, BRW-002, BRW-003, BRW-004, BRW-005, BRW-006, BRW-007, BRW-008, GATE-M6

## Milestone M8
**Tasks:** 9

- `KNW-001` — Implement evidence-backed KnowledgeCandidate — deps: GATE-M7
- `KNW-002` — Implement stale synthesis rejection — deps: KNW-001
- `KNW-003` — Implement unified Knowledge Fabric — deps: KNW-001, KNW-002, CTX-007
- `SKL-001` — Implement controlled skill intake and reconstruction — deps: KNW-003
- `SKL-002` — Implement static and security skill evaluation — deps: SKL-001, SEC-001
- `SKL-003` — Implement isolated skill execution and regression evaluation — deps: SKL-002, MAC-005
- `SKL-004` — Implement skill registry, promotion and rollback — deps: SKL-003
- `SKL-005` — Implement task-scoped skill materialization — deps: SKL-004, MAC-005
- `GATE-M8` — Milestone acceptance gate — deps: KNW-001, KNW-002, KNW-003, SKL-001, SKL-002, SKL-003, SKL-004, SKL-005, GATE-M7

## Milestone M9
**Tasks:** 9

- `BUS-001` — Implement Business Capability Pack contract — deps: GATE-M8
- `BUS-002` — Implement capability compiler intake and semantic decomposition — deps: BUS-001, KNW-003
- `BUS-003` — Implement process reconstruction and skill/workflow extraction — deps: BUS-002, SKL-004
- `BUS-004` — Bind tools, RBAC, policy and evidence to capability packs — deps: BUS-003, EXT-001
- `BUS-005` — Qualify and publish business capability packs — deps: BUS-004
- `EXT-001` — Implement canonical Tool Registry and fidelity contract — deps: GATE-M8
- `EXT-002` — Implement governed integration broker — deps: EXT-001, SEC-004, EFF-003
- `EXT-003` — Implement authenticated idempotent webhook ingress — deps: EXT-002, DAT-004
- `GATE-M9` — Milestone acceptance gate — deps: BUS-001, BUS-002, BUS-003, BUS-004, BUS-005, EXT-001, EXT-002, EXT-003, GATE-M8

## Milestone M10
**Tasks:** 9

- `AUT-001` — Implement timezone-aware logical scheduling — deps: GATE-M9
- `AUT-002` — Implement missed-fire and bounded catch-up policy — deps: AUT-001
- `AUT-003` — Re-evaluate authority on every automation fire — deps: AUT-001, SEC-001
- `AUT-004` — Implement durable pause, resume and delete semantics — deps: AUT-002, AUT-003
- `COL-001` — Implement collaboration as runtime projections — deps: RUN-005, GATE-M9
- `COL-002` — Implement durable typed handoff and message contracts — deps: COL-001
- `COL-003` — Implement durable attention and notification delivery — deps: COL-002, DAT-004
- `COL-004` — Implement persistent teammate routines — deps: AUT-004, COL-001
- `GATE-M10` — Milestone acceptance gate — deps: AUT-001, AUT-002, AUT-003, AUT-004, COL-001, COL-002, COL-003, COL-004, GATE-M9

## Milestone M11
**Tasks:** 9

- `UX-001` — Implement desktop workbench shell and navigation — deps: GATE-M10
- `UX-002` — Implement canonical event timeline and client convergence — deps: UX-001, DAT-003
- `UX-003` — Implement live browser/computer workspace pane — deps: UX-001, BRW-004
- `UX-004` — Implement exact-scope approval user experience — deps: UX-002, EFF-002
- `UX-005` — Implement artifact and evidence exploration — deps: UX-002, DAT-006
- `UX-006` — Implement web client on canonical commands and events — deps: UX-002
- `UX-007` — Implement mobile attention and continuation client — deps: UX-002, COL-003
- `UX-008` — Implement packaged command-line client — deps: UX-002
- `GATE-M11` — Milestone acceptance gate — deps: UX-001, UX-002, UX-003, UX-004, UX-005, UX-006, UX-007, UX-008, GATE-M10

## Milestone M12
**Tasks:** 9

- `SRE-001` — Implement end-to-end telemetry correlation — deps: GATE-M11
- `SRE-002` — Implement SLI and SLO measurement — deps: SRE-001
- `SRE-003` — Implement RecoveryConsistencyPoint — deps: SRE-001, MAC-007, EFF-003
- `SRE-004` — Qualify backup and restore objectives — deps: SRE-003
- `SRE-005` — Qualify load, soak and degradation behavior — deps: SRE-002
- `SRE-006` — Implement tenant quota and cost controls — deps: RUN-007, SRE-001
- `SEC-006` — Run cross-tenant adversarial qualification — deps: SRE-003, DAT-008, MAC-008
- `SEC-007` — Qualify build and artifact provenance — deps: GOV-004, SRE-005
- `GATE-M12` — Milestone acceptance gate — deps: SEC-006, SEC-007, SRE-001, SRE-002, SRE-003, SRE-004, SRE-005, SRE-006, GATE-M11

## Milestone M13
**Tasks:** 9

- `QA-001` — Qualify persistent teammate and worker vertical — deps: GATE-M12
- `QA-002` — Qualify model gateway vertical — deps: GATE-M12, MOD-008
- `QA-003` — Qualify evidence-first research vertical — deps: GATE-M12, CTX-008
- `QA-004` — Qualify protected and financial effect vertical — deps: GATE-M12, EFF-003, BRW-003
- `QA-005` — Qualify machine, browser and endpoint vertical — deps: GATE-M12, BRW-008, MAC-008
- `QA-006` — Qualify skill and business capability vertical — deps: GATE-M12, BUS-005, SKL-005
- `QA-007` — Qualify automation and multi-client convergence — deps: GATE-M12, AUT-004, UX-008
- `QA-008` — Qualify disaster recovery and effect consistency — deps: GATE-M12, SRE-004
- `GATE-M13` — Milestone acceptance gate — deps: QA-001, QA-002, QA-003, QA-004, QA-005, QA-006, QA-007, QA-008, GATE-M12

## Milestone M14
**Tasks:** 8

- `REL-001` — Create immutable release candidate — deps: GATE-M13
- `REL-002` — Qualify exact release candidate — deps: REL-001
- `REL-003` — Deploy qualified candidate to canary — deps: REL-002
- `REL-004` — Prove canary rollback and data/effect compatibility — deps: REL-003
- `REL-005` — Record independent go or no-go decision — deps: REL-004
- `REL-006` — Seal readiness evidence bundle — deps: REL-005
- `REL-007` — Enforce sole production-ready state owner — deps: REL-006
- `GATE-M14` — Production readiness gate — deps: REL-001, REL-002, REL-003, REL-004, REL-005, REL-006, REL-007, GATE-M13

## Post-readiness production promotion
**Tasks:** 1

- `REL-008` — Promote the exact production-ready candidate — deps: GATE-M14


---

<!-- source: docs/20_ATOMIC_TASK_REGISTRY.md -->

# 20 — Atomic task registry

Generated from `registries/tasks.json`.

## ENV-001 — Provision implementation qualification environment
- Milestone: 0
- Owner: platform
- Requirements: GOV-004, DAT-002
- Dependencies: GOV-006, GOV-007
- Real boundary required: true
- Assertions:
  - **ENV-001-P01 [positive]** — Provision real relational database, durable event transport, cache/lease store and object/evidence storage with isolated test identities, health checks and teardown.
  - **ENV-001-N01 [negative]** — Replace any required durable boundary with an in-memory fake and prove qualification refuses to mark the environment ready.
  - **ENV-001-R01 [recovery]** — Restart each dependency independently and verify health detection, reconnect and teardown leave no falsely passing environment state.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M0 — Milestone acceptance gate
- Milestone: 0
- Owner: release
- Requirements: INV-008
- Dependencies: ENV-001, GOV-001, GOV-002, GOV-003, GOV-004, GOV-005, GOV-006, GOV-007
- Real boundary required: false
- Assertions:
  - **GATE-M0-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M0 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M0-N01 [negative]** — Remove or fail one blocking predecessor for milestone M0 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M0-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M0 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## GOV-001 — Adopt repository into canonical ownership
- Milestone: 0
- Owner: architecture
- Requirements: GOV-001, INV-007
- Dependencies: none
- Real boundary required: false
- Assertions:
  - **GOV-001-P01 [positive]** — Generate a deterministic inventory of production entrypoints, durable stores, runtime/model/tool/browser paths and map each to exactly one canonical owner or explicit BUILD disposition.
  - **GOV-001-N01 [negative]** — Introduce an unregistered production entrypoint or alternate task/model/effect store and prove the inventory check rejects the unowned path.
  - **GOV-001-R01 [recovery]** — Change one tracked ownership input, verify --check detects drift, regenerate, then verify the inventory returns to a deterministic clean state.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GOV-002 — Freeze canonical service and state ownership
- Milestone: 0
- Owner: architecture
- Requirements: INV-001, INV-006, GOV-001
- Dependencies: GOV-001
- Real boundary required: false
- Assertions:
  - **GOV-002-P01 [positive]** — Publish one machine-readable ownership map covering every canonical service, authoritative store, event producer and external-effect actuator with no duplicate owner.
  - **GOV-002-N01 [negative]** — Assign the same authoritative state or external effect to two owners and verify ownership validation fails with both conflicting identifiers.
  - **GOV-002-R01 [recovery]** — Remove one canonical owner entry, verify dependent wiring becomes invalid, restore the owner and regenerate affected views.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GOV-003 — Install canonical schema and generated-binding gate
- Milestone: 0
- Owner: protocol
- Requirements: GOV-002, INV-007
- Dependencies: GOV-001, GOV-002
- Real boundary required: false
- Assertions:
  - **GOV-003-P01 [positive]** — Validate every registered canonical contract and generate language bindings from the registered schema revision without hand-written competing DTOs.
  - **GOV-003-N01 [negative]** — Add a required field to a hand-written shadow DTO while leaving the schema unchanged and prove the import/contract gate rejects the competing contract.
  - **GOV-003-R01 [recovery]** — Regenerate bindings after a compatible schema edit and prove no stale generated binding remains referenced by production code.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GOV-004 — Make authority generation deterministic
- Milestone: 0
- Owner: release
- Requirements: GOV-002
- Dependencies: GOV-002, GOV-003
- Real boundary required: false
- Assertions:
  - **GOV-004-P01 [positive]** — Regenerate task graph, inverse requirement links, milestone counts, reading views, support mappings and integrity metadata twice and obtain byte-identical canonical outputs.
  - **GOV-004-N01 [negative]** — Hand-edit a generated task edge or milestone count and prove check mode fails rather than accepting the stale generated view.
  - **GOV-004-R01 [recovery]** — Delete one generated view, rerun generation, and prove it is restored solely from canonical registries.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GOV-005 — Enforce production-source completeness scan
- Milestone: 0
- Owner: quality
- Requirements: GOV-003, INV-008
- Dependencies: GOV-003
- Real boundary required: false
- Assertions:
  - **GOV-005-P01 [positive]** — Scan the qualified production tree and fail on reachable incomplete implementation markers while excluding only registered test, fixture, vendor and generated paths.
  - **GOV-005-N01 [negative]** — Place an incomplete production branch behind a reachable API path and prove the scanner fails even when all task metadata claims PASS.
  - **GOV-005-R01 [recovery]** — Move the same marker into an isolated test fixture and prove production scanning remains clean without broadening exclusions.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GOV-006 — Enforce reproducible completion evidence
- Milestone: 0
- Owner: quality
- Requirements: GOV-004, INV-008
- Dependencies: GOV-003, GOV-004, GOV-005
- Real boundary required: false
- Assertions:
  - **GOV-006-P01 [positive]** — Validate PASS evidence only when the referenced task, exact requirement/assertion set, reachable repository commit, report digest, artifact digests and required real-boundary proof all match actual state.
  - **GOV-006-N01 [negative]** — Submit a report whose outer record says PASS while a blocking assertion says FAIL or whose artifact digest is substituted; both must be rejected.
  - **GOV-006-R01 [recovery]** — Record a genuine unavailable external dependency as BLOCKED_REAL_BOUNDARY and prove it remains non-completing until new evidence is produced after the boundary becomes available.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GOV-007 — Establish architecture-decision and threat-model workflow
- Milestone: 0
- Owner: architecture
- Requirements: GOV-005, INV-006, INV-004, INV-010
- Dependencies: GOV-002
- Real boundary required: false
- Assertions:
  - **GOV-007-P01 [positive]** — Create decision records that capture owner, context, chosen option, rejected alternatives, affected invariants, threat impact, migration/rollback plan and review trigger.
  - **GOV-007-N01 [negative]** — Attempt to change a canonical owner or effect/security invariant without an accepted decision record and prove CI blocks the change.
  - **GOV-007-R01 [recovery]** — Exercise a reversible decision rollback and verify generated ownership/wiring returns to the prior accepted state without orphaned schema or task references.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## DAT-001 — Implement tenant and authenticated session authority
- Milestone: 1
- Owner: api
- Requirements: DAT-001, SEC-006
- Dependencies: GATE-M0
- Real boundary required: true
- Assertions:
  - **DAT-001-P01 [positive]** — Authenticate a user into one tenant/workspace and prove every emitted command carries server-resolved tenant, user, session and workspace identity.
  - **DAT-001-N01 [negative]** — Modify a client-supplied tenant or user identifier and verify the server ignores/rejects it before any authoritative read or write.
  - **DAT-001-R01 [recovery]** — Restart the API process and prove a valid durable session can resume without recreating tenant or user authority from client state.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## DAT-002 — Create authoritative relational schema and migrations
- Milestone: 1
- Owner: data
- Requirements: DAT-002, INV-007
- Dependencies: GATE-M0
- Real boundary required: true
- Assertions:
  - **DAT-002-P01 [positive]** — Apply migrations on an empty database and create tenant-scoped tables for identities, agents, runs, graphs, protocol state, approvals, effects, schedules and registries.
  - **DAT-002-N01 [negative]** — Attempt a cross-tenant key/reference insertion and prove database/application constraints reject the invalid ownership.
  - **DAT-002-R01 [recovery]** — Upgrade then rollback the latest reversible migration on a production-like copy and verify schema/data invariants and migration history remain consistent.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## DAT-003 — Implement canonical RuntimeEvent append and replay
- Milestone: 1
- Owner: runtime
- Requirements: DAT-003, RUN-008
- Dependencies: DAT-002
- Real boundary required: true
- Assertions:
  - **DAT-003-P01 [positive]** — Append events with stable event_id, tenant/workspace/run identity, canonical sequence, causal parents, producer identity, generation and committed timestamp; replay reproduces canonical order.
  - **DAT-003-N01 [negative]** — Submit duplicate event_id or non-monotonic canonical sequence for one run and verify append fails without corrupting replay.
  - **DAT-003-R01 [recovery]** — Crash after transaction commit but before client delivery, reconnect from prior cursor, and prove the committed event is delivered exactly as projection data without re-executing work.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## DAT-004 — Implement transactional outbox delivery
- Milestone: 1
- Owner: data
- Requirements: DAT-004
- Dependencies: DAT-003
- Real boundary required: true
- Assertions:
  - **DAT-004-P01 [positive]** — Commit authoritative state mutation and its outbox record in one transaction; delivery eventually publishes the exact committed event and marks only that delivery complete.
  - **DAT-004-N01 [negative]** — Force database rollback after outbox preparation and prove no event for the rolled-back mutation appears on the durable event transport.
  - **DAT-004-R01 [recovery]** — Crash the publisher after transport publish but before outbox acknowledgement and prove restart redelivery is deduplicated by event identity.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## DAT-005 — Persist resumable protocol state
- Milestone: 1
- Owner: runtime
- Requirements: DAT-005, INV-003
- Dependencies: DAT-002, DAT-003
- Real boundary required: true
- Assertions:
  - **DAT-005-P01 [positive]** — Persist tool calls, approval waits, questions, worker lifecycle, browser/control ownership, cancellation and durable wait state independently of semantic memory.
  - **DAT-005-N01 [negative]** — Delete semantic memory while preserving protocol state and prove an interrupted approval/tool wait can still resume correctly.
  - **DAT-005-R01 [recovery]** — Restart runtime during an outstanding question/approval and prove the exact protocol object is restored without creating a duplicate request.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## DAT-006 — Implement immutable artifact and evidence storage
- Milestone: 1
- Owner: artifact
- Requirements: DAT-006
- Dependencies: DAT-002, ENV-001
- Real boundary required: true
- Assertions:
  - **DAT-006-P01 [positive]** — Store an artifact by digest with tenant, media type, producer, size, scan state and grant metadata; refetch returns bytes matching the recorded digest.
  - **DAT-006-N01 [negative]** — Attempt to overwrite an existing digest identity with different bytes and verify storage rejects mutation rather than changing historical evidence.
  - **DAT-006-R01 [recovery]** — Restore object metadata from backup and verify all referenced blobs are digest-verified before the restored artifact becomes readable.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## DAT-007 — Constrain cache and lease store to non-authoritative use
- Milestone: 1
- Owner: platform
- Requirements: DAT-002, INV-007
- Dependencies: DAT-002, DAT-005
- Real boundary required: true
- Assertions:
  - **DAT-007-P01 [positive]** — Use cache only for leases, bounded acceleration and ephemeral coordination while every recoverable task/approval/effect remains reconstructible without cache contents.
  - **DAT-007-N01 [negative]** — Flush the complete cache during active non-effect work and verify no canonical task, approval or event truth is lost or rewritten.
  - **DAT-007-R01 [recovery]** — Restart cache and verify leases/generations are safely reacquired or invalidated from authoritative state before execution resumes.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## DAT-008 — Enforce tenant-safe repository/query layer
- Milestone: 1
- Owner: data
- Requirements: SEC-006, DAT-002
- Dependencies: DAT-002, DAT-001
- Real boundary required: true
- Assertions:
  - **DAT-008-P01 [positive]** — Execute canonical repository queries under two tenants and prove identical object identifiers cannot cross tenant scope through list, get, update or event projection.
  - **DAT-008-N01 [negative]** — Inject a foreign tenant identifier into direct repository parameters and verify access is denied before data materialization.
  - **DAT-008-R01 [recovery]** — Recover from database failover and rerun isolation probes to prove connection reestablishment does not drop tenant filters.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M1 — Milestone acceptance gate
- Milestone: 1
- Owner: release
- Requirements: INV-008
- Dependencies: DAT-001, DAT-002, DAT-003, DAT-004, DAT-005, DAT-006, DAT-007, DAT-008, SEC-001, GATE-M0
- Real boundary required: false
- Assertions:
  - **GATE-M1-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M1 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M1-N01 [negative]** — Remove or fail one blocking predecessor for milestone M1 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M1-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M1 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## SEC-001 — Implement foundational immutable CapabilitySnapshot
- Milestone: 1
- Owner: security
- Requirements: SEC-001, INV-009
- Dependencies: DAT-001, DAT-005
- Real boundary required: true
- Assertions:
  - **SEC-001-P01 [positive]** — Persist an immutable CapabilitySnapshot with capability atoms, target/data constraints, expiry, parent reference and revision; prove child snapshots are strict subsets before any worker/model/tool/machine admission.
  - **SEC-001-N01 [negative]** — Attempt child capability escalation or post-admission snapshot mutation and verify both are denied before the requested execution becomes externally visible.
  - **SEC-001-R01 [recovery]** — Expire a snapshot during a durable wait and prove resumed work requires fresh admission before any further protected or consequential execution.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M2 — Milestone acceptance gate
- Milestone: 2
- Owner: release
- Requirements: INV-008
- Dependencies: RUN-001, RUN-002, RUN-003, RUN-004, RUN-005, RUN-006, RUN-007, RUN-008, GATE-M1
- Real boundary required: false
- Assertions:
  - **GATE-M2-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M2 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M2-N01 [negative]** — Remove or fail one blocking predecessor for milestone M2 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M2-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M2 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## RUN-001 — Implement canonical WorkGraph persistence
- Milestone: 2
- Owner: runtime
- Requirements: RUN-001, INV-001
- Dependencies: GATE-M1
- Real boundary required: true
- Assertions:
  - **RUN-001-P01 [positive]** — Create, version and resume a WorkGraph whose nodes, edges, dependencies, deadlines and state are persisted and mutated only by GraphTransaction.
  - **RUN-001-N01 [negative]** — Attempt a direct node-state update outside GraphTransaction and prove the repository/runtime guard rejects it.
  - **RUN-001-R01 [recovery]** — Crash between two graph transitions and prove replay resumes from the last committed transaction without duplicating completed nodes.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## RUN-002 — Implement AgentGraph lifecycle
- Milestone: 2
- Owner: runtime
- Requirements: RUN-002
- Dependencies: RUN-001, SEC-001
- Real boundary required: true
- Assertions:
  - **RUN-002-P01 [positive]** — Create a persistent teammate and an ephemeral worker with distinct lifecycle, owner, workspace binding and immutable admitted capability snapshot.
  - **RUN-002-N01 [negative]** — Attempt to reuse an expired ephemeral worker identity as a persistent teammate and verify lifecycle validation rejects the transition.
  - **RUN-002-R01 [recovery]** — Restart runtime while a persistent teammate is idle and prove identity/workspace binding survives while expired ephemeral state is cleaned safely.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## RUN-003 — Implement StateGraph and GraphTransaction
- Milestone: 2
- Owner: runtime
- Requirements: RUN-001
- Dependencies: RUN-001, DAT-003
- Real boundary required: true
- Assertions:
  - **RUN-003-P01 [positive]** — Apply a multi-object graph transition atomically and emit the corresponding RuntimeEvent only after all state preconditions succeed.
  - **RUN-003-N01 [negative]** — Force one precondition failure in a multi-object transaction and verify no partial graph/agent/state mutation or event remains committed.
  - **RUN-003-R01 [recovery]** — Crash after database commit before projection delivery and prove transaction identity prevents a second state mutation during recovery.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## RUN-004 — Implement transactional worker admission
- Milestone: 2
- Owner: runtime
- Requirements: RUN-003, SEC-001, INV-009
- Dependencies: RUN-002, RUN-003, SEC-001
- Real boundary required: true
- Assertions:
  - **RUN-004-P01 [positive]** — Reserve worker capacity, budget and child capability atomically before exposing a worker dispatch; child authority is a strict subset of the parent.
  - **RUN-004-N01 [negative]** — Request a child capability or budget ceiling above the parent allowance and verify admission fails before worker visibility or resource consumption.
  - **RUN-004-R01 [recovery]** — Crash after reservation but before dispatch and prove recovery either completes the original admission once or releases the orphaned reservation.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## RUN-005 — Implement asynchronous fan-out and fan-in
- Milestone: 2
- Owner: runtime
- Requirements: RUN-004, RUN-008
- Dependencies: RUN-004
- Real boundary required: true
- Assertions:
  - **RUN-005-P01 [positive]** — Dispatch at least 32 child turns, persist each dispatch and incremental outcome independently, and aggregate partial/final results without blocking parent lifecycle.
  - **RUN-005-N01 [negative]** — Deliver one child result twice and another after its deadline; verify deduplication and deadline semantics do not corrupt aggregate state.
  - **RUN-005-R01 [recovery]** — Disconnect all clients while children complete, then reconnect and prove completed outcomes appear from durable state without child re-execution.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## RUN-006 — Implement effect-aware cancellation
- Milestone: 2
- Owner: runtime
- Requirements: RUN-005, EFF-004
- Dependencies: RUN-005
- Real boundary required: true
- Assertions:
  - **RUN-006-P01 [positive]** — Cancel a parent with queued, running and already-effect-committed children; prevent queued starts, request running cancellation and preserve committed effect history.
  - **RUN-006-N01 [negative]** — Attempt to mark a committed external effect as rolled back solely because its parent was cancelled and verify the state transition is rejected.
  - **RUN-006-R01 [recovery]** — Restart during cancellation and prove every child reaches an explicit terminal/cancellation state without replaying committed effects.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## RUN-007 — Implement atomic hierarchical budget reservation
- Milestone: 2
- Owner: runtime
- Requirements: RUN-006, MOD-005
- Dependencies: RUN-004
- Real boundary required: true
- Assertions:
  - **RUN-007-P01 [positive]** — Race at least 32 concurrent reservations against one parent ceiling and prove accepted reservations plus committed usage never exceed the available parent budget.
  - **RUN-007-N01 [negative]** — Retry the same reservation idempotency key and submit a stale-generation reservation; duplicate spend and stale admission must both be rejected.
  - **RUN-007-R01 [recovery]** — Cancel work before final provider usage arrives and prove the reservation remains settling until late usage is applied exactly once and unused amount is released.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## RUN-008 — Implement durable waits and callbacks
- Milestone: 2
- Owner: runtime
- Requirements: RUN-007
- Dependencies: RUN-003, DAT-005
- Real boundary required: true
- Assertions:
  - **RUN-008-P01 [positive]** — Suspend a graph on timer, approval and external callback waits without holding a process and resume each from a durable wait identity.
  - **RUN-008-N01 [negative]** — Deliver the same callback twice and an expired callback after cancellation; verify only the first valid callback advances the graph.
  - **RUN-008-R01 [recovery]** — Restart runtime and event transport during a pending wait and prove the graph resumes exactly once when the wait condition later becomes true.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M3 — Milestone acceptance gate
- Milestone: 3
- Owner: release
- Requirements: INV-008
- Dependencies: MOD-001, MOD-002, MOD-003, MOD-004, MOD-005, MOD-006, MOD-007, MOD-008, GATE-M2
- Real boundary required: false
- Assertions:
  - **GATE-M3-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M3 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M3-N01 [negative]** — Remove or fail one blocking predecessor for milestone M3 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M3-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M3 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## MOD-001 — Establish model gateway as exclusive fulfillment boundary
- Milestone: 3
- Owner: model
- Requirements: MOD-001, INV-005
- Dependencies: GATE-M2
- Real boundary required: true
- Assertions:
  - **MOD-001-P01 [positive]** — Route every production model request from API/runtime through the model gateway and prove clients, guests, tools, skills and connectors contain no provider credential path.
  - **MOD-001-N01 [negative]** — Enable a direct provider call from a worker/tool code path and prove source/import/runtime policy gates reject that route.
  - **MOD-001-R01 [recovery]** — Restart the gateway during an admitted request and return a typed interruption/retry outcome without transferring credential custody elsewhere.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MOD-002 — Implement provider-neutral adapter contract
- Milestone: 3
- Owner: model
- Requirements: MOD-002
- Dependencies: MOD-001
- Real boundary required: true
- Assertions:
  - **MOD-002-P01 [positive]** — Translate one enabled provider profile into canonical request, stream, usage and terminal events while keeping provider-specific fields inside the adapter boundary.
  - **MOD-002-N01 [negative]** — Return a provider payload with missing mandatory identity/usage fields and prove the adapter emits a typed protocol failure rather than fabricating values.
  - **MOD-002-R01 [recovery]** — Disable the adapter during an in-flight request and verify gateway state reaches an explicit terminal outcome and reservations remain reconcilable.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MOD-003 — Implement deterministic capability-demand routing
- Milestone: 3
- Owner: model
- Requirements: MOD-003
- Dependencies: MOD-001, RUN-007
- Real boundary required: true
- Assertions:
  - **MOD-003-P01 [positive]** — Select an allowed model profile from capability demand, policy, residency, context, availability and budget using a versioned deterministic route decision.
  - **MOD-003-N01 [negative]** — Remove all candidates satisfying residency or budget constraints and verify routing fails explicitly without making a prerequisite model call.
  - **MOD-003-R01 [recovery]** — Change catalog availability between retry attempts and prove the recorded routing version plus retry policy prevents silent route drift for an already admitted step.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MOD-004 — Implement canonical streaming, cancellation and backpressure
- Milestone: 3
- Owner: model
- Requirements: MOD-004
- Dependencies: MOD-002, MOD-003
- Real boundary required: true
- Assertions:
  - **MOD-004-P01 [positive]** — Emit MODEL_STARTED followed by ordered deltas/tool proposals/usage and exactly one terminal event while respecting consumer backpressure.
  - **MOD-004-N01 [negative]** — Inject duplicate sequence, pre-start delta and post-terminal delta; each invalid stream condition must be rejected or normalized without reaching runtime as valid events.
  - **MOD-004-R01 [recovery]** — Cancel during blocked downstream consumption and prove provider cancellation, terminal MODEL_CANCELLED and reservation settlement complete without deadlock.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MOD-005 — Implement usage reservation and late settlement
- Milestone: 3
- Owner: model
- Requirements: MOD-005, RUN-006
- Dependencies: MOD-004, RUN-007
- Real boundary required: true
- Assertions:
  - **MOD-005-P01 [positive]** — Reserve usage before provider start, apply streamed/final usage idempotently, and release unused reservation only after usage finality.
  - **MOD-005-N01 [negative]** — Deliver the same late charge twice after cancellation and verify the second delivery produces no additional spend; an over-ceiling adjustment triggers policy handling.
  - **MOD-005-R01 [recovery]** — Recover from gateway restart with SETTLING_PROVIDER_USAGE records and complete append-only adjustments without rewriting earlier settlement history.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MOD-006 — Implement model privacy and residency enforcement
- Milestone: 3
- Owner: security
- Requirements: MOD-006, SEC-003
- Dependencies: MOD-001, DAT-001
- Real boundary required: true
- Assertions:
  - **MOD-006-P01 [positive]** — Classify request context before provider egress and enforce allow/redact/deny/residency policy with auditable policy decision identity.
  - **MOD-006-N01 [negative]** — Place protected content in prompt/context for a denied destination and prove captured outbound bytes contain zero protected content.
  - **MOD-006-R01 [recovery]** — Restart policy dependency during admission and fail closed until a valid current decision is obtained; do not send while decision state is unknown.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MOD-007 — Implement provider failure isolation and failover
- Milestone: 3
- Owner: model
- Requirements: MOD-004, MOD-003
- Dependencies: MOD-004, MOD-005
- Real boundary required: true
- Assertions:
  - **MOD-007-P01 [positive]** — Convert timeout, rate-limit, malformed response and provider outage into typed outcomes and use only policy-allowed failover candidates.
  - **MOD-007-N01 [negative]** — Trigger failover after a tool proposal/effect boundary has already committed and prove the gateway cannot silently replay the committed external effect.
  - **MOD-007-R01 [recovery]** — Restore a provider after outage and verify health re-entry requires fresh probe state before it becomes routable.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MOD-008 — Qualify enabled model profile at real boundary
- Milestone: 3
- Owner: quality
- Requirements: MOD-007
- Dependencies: MOD-005, MOD-006, MOD-007
- Real boundary required: true
- Assertions:
  - **MOD-008-P01 [positive]** — Execute real request, streaming, cancellation, usage, malformed-response handling and outage/failover tests for the enabled profile and bind results to exact adapter/config artifacts.
  - **MOD-008-N01 [negative]** — Run the qualification with real_boundary=false or without actual provider response evidence and verify completion evidence is rejected.
  - **MOD-008-R01 [recovery]** — Repeat the suite after gateway restart and confirm result/usage identities remain reproducible and no stale request is resumed as a new charge.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## CTX-001 — Implement typed bounded SearchProgram
- Milestone: 4
- Owner: context
- Requirements: CTX-001
- Dependencies: GATE-M3
- Real boundary required: true
- Assertions:
  - **CTX-001-P01 [positive]** — Validate and execute programs using only SEARCH, RETRIEVE, FAN_OUT, FILTER, RANK, DEDUPLICATE, JOIN, EXTRACT, RESOLVE_ENTITY, VERIFY, ITERATE and SYNTHESIZE with typed arguments and bounded budgets.
  - **CTX-001-N01 [negative]** — Submit executable predicate text, unknown operator, fan-out above 1000 or iteration above 20 and verify validation fails before network/tool execution.
  - **CTX-001-R01 [recovery]** — Restart during a multi-stage program and resume from durable operator outputs without repeating completed retrieval/effect-free steps unnecessarily.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## CTX-002 — Implement retrieval adapters and source provenance
- Milestone: 4
- Owner: context
- Requirements: CTX-002
- Dependencies: CTX-001
- Real boundary required: true
- Assertions:
  - **CTX-002-P01 [positive]** — Retrieve sources with canonical source identity, retrieval timestamp, freshness metadata, access status, content digest and deduplication key.
  - **CTX-002-N01 [negative]** — Return two URLs/documents resolving to the same canonical content/entity and verify duplicate candidates are merged without losing distinct provenance.
  - **CTX-002-R01 [recovery]** — When a source becomes inaccessible, preserve prior provenance as stale/inaccessible rather than claiming fresh verification.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## CTX-003 — Implement ResearchRecord and entity resolution
- Milestone: 4
- Owner: context
- Requirements: CTX-003
- Dependencies: CTX-002
- Real boundary required: true
- Assertions:
  - **CTX-003-P01 [positive]** — Produce records separating canonical entity identity, attributes, claims, source references, freshness, confidence and verification state.
  - **CTX-003-N01 [negative]** — Merge two different entities with similar names and verify identity constraints/evidence detect the false merge before final synthesis.
  - **CTX-003-R01 [recovery]** — Correct an entity identity after new evidence and preserve superseded identity evidence without silently rewriting prior records.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## CTX-004 — Implement wide and deep research execution
- Milestone: 4
- Owner: context
- Requirements: CTX-004
- Dependencies: CTX-001, CTX-003
- Real boundary required: true
- Assertions:
  - **CTX-004-P01 [positive]** — Discover and enrich at least 100 candidates using bounded parallel fan-out, joins, deduplication and durable intermediate result sets under explicit cost/time limits.
  - **CTX-004-N01 [negative]** — Force one retrieval branch to exceed budget and another to time out; verify bounded partial completion and explicit missing-data status rather than unbounded retries.
  - **CTX-004-R01 [recovery]** — Restart context/runtime mid-research and continue from persisted intermediate sets while preserving operator provenance and budget state.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## CTX-005 — Implement independent claim and source verification
- Milestone: 4
- Owner: context
- Requirements: CTX-005
- Dependencies: CTX-002, CTX-003
- Real boundary required: true
- Assertions:
  - **CTX-005-P01 [positive]** — Independently refetch cited sources and classify each claim as supported, unsupported, stale, inaccessible or conflicting with evidence references.
  - **CTX-005-N01 [negative]** — Alter a synthesized claim while keeping its citation unchanged and verify support scoring fails the claim rather than trusting citation presence.
  - **CTX-005-R01 [recovery]** — When refetch transitions from accessible to inaccessible, retain the last evidence digest and mark verification state accordingly without fabricating freshness.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## CTX-006 — Implement bounded Context Projection
- Milestone: 4
- Owner: context
- Requirements: CTX-007, INV-003
- Dependencies: CTX-005, DAT-005
- Real boundary required: true
- Assertions:
  - **CTX-006-P01 [positive]** — Build task-scoped model context from canonical history, knowledge, tool outputs and evidence under token/data/capability limits with projection version identity.
  - **CTX-006-N01 [negative]** — Request context from a forbidden tenant/data class or exceed projection budget and verify protected material is omitted/denied before model request construction.
  - **CTX-006-R01 [recovery]** — Invalidate a source epoch and rebuild projection without changing canonical transcript, protocol state or recovery state.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## CTX-007 — Implement index freshness and tombstone semantics
- Milestone: 4
- Owner: indexer
- Requirements: CTX-002
- Dependencies: CTX-002, DAT-006
- Real boundary required: true
- Assertions:
  - **CTX-007-P01 [positive]** — Ingest, update and tombstone indexed material with source revision, chunk provenance and freshness watermark; queries exclude tombstoned content by default.
  - **CTX-007-N01 [negative]** — Delete a source without publishing a tombstone and verify freshness validation detects index/source divergence.
  - **CTX-007-R01 [recovery]** — Rebuild the index from authoritative source/artifact metadata and prove query identity/freshness semantics remain consistent after index loss.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## CTX-008 — Qualify reproducible research scoring
- Milestone: 4
- Owner: quality
- Requirements: CTX-006
- Dependencies: CTX-004, CTX-005, CTX-007
- Real boundary required: true
- Assertions:
  - **CTX-008-P01 [positive]** — Run a sealed benchmark and achieve discovery recall >=0.90, entity precision >=0.95, claim precision >=0.95, citation support >=0.98, freshness >=0.98, duplicate rate <=0.02 and hard completion >=0.85.
  - **CTX-008-N01 [negative]** — Change scorer formula, dataset digest or source policy without updating qualification identity and prove the result is rejected as non-comparable.
  - **CTX-008-R01 [recovery]** — Re-run scoring from preserved benchmark outputs and obtain identical metric values within declared deterministic tolerance.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M4 — Milestone acceptance gate
- Milestone: 4
- Owner: release
- Requirements: INV-008
- Dependencies: CTX-001, CTX-002, CTX-003, CTX-004, CTX-005, CTX-006, CTX-007, CTX-008, GATE-M3
- Real boundary required: false
- Assertions:
  - **GATE-M4-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M4 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M4-N01 [negative]** — Remove or fail one blocking predecessor for milestone M4 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M4-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M4 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## EFF-001 — Implement universal Effect Ledger
- Milestone: 5
- Owner: effects
- Requirements: EFF-001, EFF-004
- Dependencies: SEC-002, SEC-005
- Real boundary required: true
- Assertions:
  - **EFF-001-P01 [positive]** — Create EffectRecord before every consequential actuation and persist proposal, policy, approval, execution, outcome, receipt and evidence correlation.
  - **EFF-001-N01 [negative]** — Invoke a consequential connector/browser operation without effect_id and verify actuator/broker rejects it before external call.
  - **EFF-001-R01 [recovery]** — Restart runtime during EXECUTING and reconcile the same effect identity rather than issuing a new effect on recovery.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## EFF-002 — Implement durable scoped approvals
- Milestone: 5
- Owner: effects
- Requirements: EFF-002, EFF-005
- Dependencies: EFF-001
- Real boundary required: true
- Assertions:
  - **EFF-002-P01 [positive]** — Persist approval request and receipt bound to exact operation/effect/target/normalized scope, including payee, amount, currency and ceilings for financial effects.
  - **EFF-002-N01 [negative]** — Change approved amount by one minor currency unit or substitute payee while retaining the receipt and prove denial occurs before provider invocation.
  - **EFF-002-R01 [recovery]** — Disconnect approving client, approve from another authorized surface, and resume exactly the waiting effect without duplicate approval/effect creation.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## EFF-003 — Implement UNKNOWN effect reconciliation
- Milestone: 5
- Owner: effects
- Requirements: EFF-003, EFF-007
- Dependencies: EFF-001, EFF-002
- Real boundary required: true
- Assertions:
  - **EFF-003-P01 [positive]** — On ambiguous timeout mark the effect UNKNOWN and query provider/target idempotency state before deciding COMMITTED, FAILED or safe retry.
  - **EFF-003-N01 [negative]** — Retry an UNKNOWN effect blindly without reconciliation and verify the effect engine blocks the second actuation.
  - **EFF-003-R01 [recovery]** — Restart reconciliation worker mid-query and continue with the same effect/idempotency identity until an explicit reconciled terminal outcome is recorded.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M5 — Milestone acceptance gate
- Milestone: 5
- Owner: release
- Requirements: INV-008
- Dependencies: EFF-001, EFF-002, EFF-003, SEC-002, SEC-003, SEC-004, SEC-005, GATE-M4
- Real boundary required: false
- Assertions:
  - **GATE-M5-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M5 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M5-N01 [negative]** — Remove or fail one blocking predecessor for milestone M5 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M5-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M5 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## SEC-002 — Implement argument-bound policy decisions
- Milestone: 5
- Owner: security
- Requirements: SEC-002
- Dependencies: SEC-001
- Real boundary required: true
- Assertions:
  - **SEC-002-P01 [positive]** — Evaluate actor, semantic operation, normalized arguments, target, data classification and capability snapshot into a versioned PolicyDecision.
  - **SEC-002-N01 [negative]** — Reuse an allow decision after changing one normalized consequential argument and prove scope digest mismatch blocks execution.
  - **SEC-002-R01 [recovery]** — When policy service recovers from outage, require a fresh decision for pending consequential work rather than accepting unknown/stale policy.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SEC-003 — Implement destination-aware privacy gate
- Milestone: 5
- Owner: security
- Requirements: SEC-003, MOD-006
- Dependencies: SEC-002
- Real boundary required: true
- Assertions:
  - **SEC-003-P01 [positive]** — Classify outbound model, connector, upload and remote-worker data and apply allow/redact/approval/deny before bytes leave the trusted boundary.
  - **SEC-003-N01 [negative]** — Attempt a denied secret/PII transfer through an alternate connector/browser upload route and prove all egress paths use the same classification decision.
  - **SEC-003-R01 [recovery]** — Recover classifier dependency and re-evaluate pending egress against current policy instead of replaying a stale allow.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SEC-004 — Implement scoped credential broker
- Milestone: 5
- Owner: security
- Requirements: SEC-004
- Dependencies: SEC-002, DAT-001
- Real boundary required: true
- Assertions:
  - **SEC-004-P01 [positive]** — Issue short-lived credential handles bound to tenant, operation, target, expiry and capability without returning reusable plaintext credentials to clients/guests.
  - **SEC-004-N01 [negative]** — Replay an expired handle or use it for a different target/operation and verify broker refusal before external authentication.
  - **SEC-004-R01 [recovery]** — Rotate underlying credentials while a handle is outstanding and ensure invalidated handles fail cleanly while new handles use the rotated secret.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SEC-005 — Implement behavior-sequence guard
- Milestone: 5
- Owner: security
- Requirements: SEC-005
- Dependencies: SEC-002, SEC-003
- Real boundary required: true
- Assertions:
  - **SEC-005-P01 [positive]** — Evaluate canonical event/effect history so a configured dangerous sequence can block or escalate the next operation before actuation.
  - **SEC-005-N01 [negative]** — Perform allowed secret read followed by disallowed outbound upload sequence and verify the upload is blocked despite both operation types being independently valid in isolation.
  - **SEC-005-R01 [recovery]** — After policy/rule update, re-evaluate pending sequence state deterministically without deleting historical events.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M6 — Milestone acceptance gate
- Milestone: 6
- Owner: release
- Requirements: INV-008
- Dependencies: MAC-001, MAC-002, MAC-003, MAC-004, MAC-005, MAC-006, MAC-007, MAC-008, GATE-M5
- Real boundary required: false
- Assertions:
  - **GATE-M6-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M6 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M6-N01 [negative]** — Remove or fail one blocking predecessor for milestone M6 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M6-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M6 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## MAC-001 — Implement execution-target inventory and lifecycle
- Milestone: 6
- Owner: machine
- Requirements: MAC-001, SEC-007
- Dependencies: GATE-M5
- Real boundary required: true
- Assertions:
  - **MAC-001-P01 [positive]** — Register execution targets with tenant, type, lifecycle state, execution generation, support profile and health identity; lifecycle transitions are durable and auditable.
  - **MAC-001-N01 [negative]** — Attempt to dispatch work to an unregistered, wrong-tenant or disabled support target and verify placement rejects it before lease acquisition.
  - **MAC-001-R01 [recovery]** — Recover machine-control after restart and reconstruct target state from authoritative inventory/heartbeats without trusting stale in-memory ownership.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MAC-002 — Implement exclusive placement, lease and fence
- Milestone: 6
- Owner: machine
- Requirements: MAC-001, SEC-007
- Dependencies: MAC-001
- Real boundary required: true
- Assertions:
  - **MAC-002-P01 [positive]** — Acquire an exclusive lease and fence token for a target generation before dispatch; every guest/endpoint action validates all three.
  - **MAC-002-N01 [negative]** — Submit an action with stale generation, expired lease or prior fence token and verify rejection before guest actuation.
  - **MAC-002-R01 [recovery]** — Expire the lease during controller crash, reacquire with higher fence/generation as required, and prove the old controller can no longer act.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MAC-003 — Implement qworkerd typed guest protocol
- Milestone: 6
- Owner: worker
- Requirements: MAC-002, MAC-005
- Dependencies: MAC-002, SEC-004
- Real boundary required: true
- Assertions:
  - **MAC-003-P01 [positive]** — Execute filesystem, terminal, process and browser/computer guest operations through versioned typed RPC with bounded inputs/outputs and task-scoped capability handles.
  - **MAC-003-N01 [negative]** — Send an unknown operation version, protected path write or ambient-secret request and verify guest rejects it before touching the resource.
  - **MAC-003-R01 [recovery]** — Restart qworkerd during a non-effect operation and reconnect using target/generation identity without granting broader authority.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MAC-004 — Implement durable worker delivery, ACK and redelivery
- Milestone: 6
- Owner: worker
- Requirements: MAC-002, MAC-003
- Dependencies: MAC-003
- Real boundary required: true
- Assertions:
  - **MAC-004-P01 [positive]** — Deliver action envelopes with delivery_id, attempt, idempotency key and expiry; ACK only after the canonical result is durably recorded.
  - **MAC-004-N01 [negative]** — Drop the ACK after successful execution and redeliver the envelope; verify the worker returns the original result without re-executing the operation.
  - **MAC-004-R01 [recovery]** — Restart worker-gateway with unacknowledged deliveries and prove redelivery respects expiry, generation and idempotency.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MAC-005 — Implement isolated task runtime
- Milestone: 6
- Owner: machine
- Requirements: MAC-003, SEC-006
- Dependencies: MAC-003, SEC-003
- Real boundary required: true
- Assertions:
  - **MAC-005-P01 [positive]** — Provision an isolated per-task environment with tenant-bound identity, deny-by-default internal networking, controlled egress and no long-lived provider credentials.
  - **MAC-005-N01 [negative]** — Attempt internal-network access or unbrokered external credential use outside policy and verify the environment blocks the request.
  - **MAC-005-R01 [recovery]** — Destroy and recreate the isolated runtime from declared workspace/artifact inputs and prove no undeclared guest-local state is required for task recovery.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MAC-006 — Implement persistent workspace computer
- Milestone: 6
- Owner: machine
- Requirements: MAC-004, RUN-008
- Dependencies: MAC-002, DAT-006
- Real boundary required: true
- Assertions:
  - **MAC-006-P01 [positive]** — Bind a persistent workspace computer to its owner/workspace independently of client/session lifetime and preserve authorized files/browser state across hibernation.
  - **MAC-006-N01 [negative]** — Attach the workspace to a different tenant/user without an authorized transfer and verify machine-control refuses the binding.
  - **MAC-006-R01 [recovery]** — Hibernate, restart control services and resume the workspace while preserving identity and advancing execution generation where required.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MAC-007 — Implement checkpoint, snapshot, restore and migration
- Milestone: 6
- Owner: machine
- Requirements: MAC-006, MAC-007, SRE-003
- Dependencies: MAC-005, MAC-006, DAT-006
- Real boundary required: true
- Assertions:
  - **MAC-007-P01 [positive]** — Create workspace-only and full-machine checkpoints whose referenced database/event/artifact state is durably committed and digest-verified before RESTORABLE.
  - **MAC-007-N01 [negative]** — Mark a checkpoint restorable while one referenced artifact is missing or one state watermark is uncommitted and verify qualification rejects it.
  - **MAC-007-R01 [recovery]** — Restore/migrate to a new generation and prove stale pre-restore actions fail lease/fence/generation validation.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## MAC-008 — Implement private execution target path
- Milestone: 6
- Owner: machine
- Requirements: MAC-008
- Dependencies: MAC-004, MAC-007
- Real boundary required: true
- Assertions:
  - **MAC-008-P01 [positive]** — Register a private worker target and execute the same typed command/capability/effect/evidence protocol used by hosted targets without a separate runtime.
  - **MAC-008-N01 [negative]** — Attempt to enable a private target without its mapped qualification suites and verify support selection keeps it disabled.
  - **MAC-008-R01 [recovery]** — Disconnect the private target, preserve pending work, then reconnect or re-place safely according to operation/effect idempotency.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BRW-001 — Provision managed browser session architecture
- Milestone: 7
- Owner: browser
- Requirements: BRW-001, BRW-002
- Dependencies: GATE-M6
- Real boundary required: true
- Assertions:
  - **BRW-001-P01 [positive]** — Create a durable managed browser session bound to workspace/target with structured control channels, observation stream and viewer/controller state.
  - **BRW-001-N01 [negative]** — Attach a viewer/controller from another tenant or stale session generation and verify access is denied before browser state is exposed.
  - **BRW-001-R01 [recovery]** — Restart client/browser-control process and reconnect to the same qualified session when session health permits without silently creating a new session identity.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BRW-002 — Implement structured browser actions and observation
- Milestone: 7
- Owner: browser
- Requirements: BRW-001
- Dependencies: BRW-001
- Real boundary required: true
- Assertions:
  - **BRW-002-P01 [positive]** — Navigate, query, click, type, select and extract using structured page/accessibility/network state where available and correlate observations to run/step/session.
  - **BRW-002-N01 [negative]** — Target an element using stale page identity after navigation and verify the action is rejected/re-resolved instead of clicking an unrelated target.
  - **BRW-002-R01 [recovery]** — When structured state becomes unavailable, enter explicit degraded observation mode and recover to structured control without changing browser session identity.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BRW-003 — Enforce semantic effect classification for browser actions
- Milestone: 7
- Owner: browser
- Requirements: BRW-003, EFF-006
- Dependencies: BRW-002, EFF-001, EFF-002
- Real boundary required: true
- Assertions:
  - **BRW-003-P01 [positive]** — Classify low-level input by semantic outcome so send, publish, purchase, delete, account change or protected upload enters policy/approval/Effect Ledger before actuator execution.
  - **BRW-003-N01 [negative]** — Attempt to submit a purchase or message using a generic click/type primitive without an EffectRecord and verify browser-control refuses to actuate.
  - **BRW-003-R01 [recovery]** — After approval/policy wait, revalidate page/session/operation scope before resuming and refuse if the semantic target changed.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BRW-004 — Implement human observation and takeover
- Milestone: 7
- Owner: browser
- Requirements: BRW-002
- Dependencies: BRW-001, MAC-002
- Real boundary required: true
- Assertions:
  - **BRW-004-P01 [positive]** — Expose the live session with explicit viewer/controller identity and allow authorized human takeover and return of control without restarting browser or losing task context.
  - **BRW-004-N01 [negative]** — Let agent and human attempt control simultaneously and prove controller lease serializes actuation and exposes ownership state in UI/runtime.
  - **BRW-004-R01 [recovery]** — Disconnect the human controller unexpectedly and transition through bounded takeover-release policy before agent control can resume.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BRW-005 — Implement governed browser file transfer
- Milestone: 7
- Owner: browser
- Requirements: BRW-003, DAT-006
- Dependencies: BRW-002, DAT-006
- Real boundary required: true
- Assertions:
  - **BRW-005-P01 [positive]** — Upload/download files only through artifact records and scoped grants, recording source/target digest, scan state and browser session correlation.
  - **BRW-005-N01 [negative]** — Attempt upload from an arbitrary host path or unscanned/unauthorized artifact and verify transfer is denied before browser file selection.
  - **BRW-005-R01 [recovery]** — Interrupt a download, resume/retry with artifact identity, and verify final bytes match digest without duplicate external effects.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BRW-006 — Implement personal endpoint relay
- Milestone: 7
- Owner: endpoint
- Requirements: BRW-004, SEC-007
- Dependencies: MAC-004, EFF-001
- Real boundary required: true
- Assertions:
  - **BRW-006-P01 [positive]** — Dispatch endpoint actions containing endpoint/target identity, execution generation, lease, fence, capability, policy, effect, delivery/idempotency, operation version and expiry.
  - **BRW-006-N01 [negative]** — Remove fence/generation or alter an approval-bound argument and prove endpoint rejects before actuation.
  - **BRW-006-R01 [recovery]** — Drop response delivery after endpoint execution, reconnect and return the original result for the same idempotency key without repeating the action.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BRW-007 — Persist browser/computer observation evidence
- Milestone: 7
- Owner: browser
- Requirements: BRW-005, DAT-006
- Dependencies: BRW-002, DAT-006
- Real boundary required: true
- Assertions:
  - **BRW-007-P01 [positive]** — Store structured observations and selected visual evidence with session/step/target identity, timestamps and digests while separating observations from effect truth.
  - **BRW-007-N01 [negative]** — Replay an observation as though it were a command/result capable of re-actuation and verify consumers treat it as evidence only.
  - **BRW-007-R01 [recovery]** — Recover after evidence-store outage by preserving canonical action/result state and backfilling missing eligible evidence without rerunning the action.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BRW-008 — Qualify enabled browser and endpoint profiles
- Milestone: 7
- Owner: quality
- Requirements: BRW-006, BRW-002
- Dependencies: BRW-003, BRW-004, BRW-005, BRW-006, BRW-007
- Real boundary required: true
- Assertions:
  - **BRW-008-P01 [positive]** — Run real navigation, structured action, consequential-action classification, takeover, reconnect, file-transfer and stale-envelope tests for every enabled profile.
  - **BRW-008-N01 [negative]** — Attempt to enable a profile lacking one mapped blocking test or real-boundary proof and verify support validation keeps it disabled.
  - **BRW-008-R01 [recovery]** — Repeat qualification after browser/endpoint process restart and confirm durable session/action identities remain consistent.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M7 — Milestone acceptance gate
- Milestone: 7
- Owner: release
- Requirements: INV-008
- Dependencies: BRW-001, BRW-002, BRW-003, BRW-004, BRW-005, BRW-006, BRW-007, BRW-008, GATE-M6
- Real boundary required: false
- Assertions:
  - **GATE-M7-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M7 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M7-N01 [negative]** — Remove or fail one blocking predecessor for milestone M7 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M7-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M7 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## GATE-M8 — Milestone acceptance gate
- Milestone: 8
- Owner: release
- Requirements: INV-008
- Dependencies: KNW-001, KNW-002, KNW-003, SKL-001, SKL-002, SKL-003, SKL-004, SKL-005, GATE-M7
- Real boundary required: false
- Assertions:
  - **GATE-M8-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M8 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M8-N01 [negative]** — Remove or fail one blocking predecessor for milestone M8 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M8-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M8 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## KNW-001 — Implement evidence-backed KnowledgeCandidate
- Milestone: 8
- Owner: knowledge
- Requirements: KNW-001
- Dependencies: GATE-M7
- Real boundary required: true
- Assertions:
  - **KNW-001-P01 [positive]** — Create candidates with provenance, evidence references, source epoch, confidence, validity interval, conflict set and producer/run identity before durable acceptance.
  - **KNW-001-N01 [negative]** — Submit a candidate with missing provenance/evidence or authority outside its source scope and verify qualification rejects it.
  - **KNW-001-R01 [recovery]** — When source evidence is withdrawn/tombstoned, retain candidate history and update validity/conflict state rather than deleting provenance.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## KNW-002 — Implement stale synthesis rejection
- Milestone: 8
- Owner: knowledge
- Requirements: KNW-002
- Dependencies: KNW-001
- Real boundary required: true
- Assertions:
  - **KNW-002-P01 [positive]** — Tag asynchronous synthesis with source/task epochs and accept only when all relevant epochs still match at commit time.
  - **KNW-002-N01 [negative]** — Change/fork/revert the source task while synthesis is running and prove the stale result cannot enter active knowledge.
  - **KNW-002-R01 [recovery]** — Restart synthesis worker and recompute from current epoch while preserving the rejected stale attempt as diagnostic evidence.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## KNW-003 — Implement unified Knowledge Fabric
- Milestone: 8
- Owner: knowledge
- Requirements: KNW-003, INV-003
- Dependencies: KNW-001, KNW-002, CTX-007
- Real boundary required: true
- Assertions:
  - **KNW-003-P01 [positive]** — Store/query enterprise, user-authorized, research, successful-work and engineering knowledge through one versioned fabric with tenant/source/evidence scope.
  - **KNW-003-N01 [negative]** — Try to recover a run solely from Knowledge Fabric after deleting protocol/checkpoint state and verify recovery refuses rather than treating memory as canonical state.
  - **KNW-003-R01 [recovery]** — Reindex/rebuild knowledge projections from durable candidates/evidence and preserve canonical source identities across projection loss.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SKL-001 — Implement controlled skill intake and reconstruction
- Milestone: 8
- Owner: skills
- Requirements: SKL-001
- Dependencies: KNW-003
- Real boundary required: true
- Assertions:
  - **SKL-001-P01 [positive]** — Convert authoritative documents/procedures/examples into candidate SkillPackages with declared purpose, inputs, outputs, instructions, dependencies and source scope.
  - **SKL-001-N01 [negative]** — Create a candidate from untrusted/unscoped material or omit intended-use/exclusion metadata and verify intake keeps it unqualified.
  - **SKL-001-R01 [recovery]** — Update source material and create a new candidate version while preserving provenance and keeping the prior qualified version available until promotion decision.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SKL-002 — Implement static and security skill evaluation
- Milestone: 8
- Owner: skills
- Requirements: SKL-002, SKL-003
- Dependencies: SKL-001, SEC-001
- Real boundary required: true
- Assertions:
  - **SKL-002-P01 [positive]** — Analyze candidate package for schema validity, forbidden authority expansion, unsafe helper behavior, protected paths, network needs and declared tool/capability usage.
  - **SKL-002-N01 [negative]** — Embed a helper that attempts undeclared network/credential access or self-promotion and verify evaluation blocks promotion.
  - **SKL-002-R01 [recovery]** — After evaluator update, re-evaluate affected candidate versions without silently changing already-recorded evaluation evidence.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SKL-003 — Implement isolated skill execution and regression evaluation
- Milestone: 8
- Owner: skills
- Requirements: SKL-002
- Dependencies: SKL-002, MAC-005
- Real boundary required: true
- Assertions:
  - **SKL-003-P01 [positive]** — Run candidate skill cases in isolated task runtimes with declared capabilities and compare outputs/effects/evidence to versioned thresholds and regressions.
  - **SKL-003-N01 [negative]** — Make the candidate pass only when a mock external boundary is substituted for a required real boundary and verify qualification remains blocked.
  - **SKL-003-R01 [recovery]** — Crash evaluation runtime mid-case and resume/restart the case with clean isolation so partial state cannot fabricate a pass.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SKL-004 — Implement skill registry, promotion and rollback
- Milestone: 8
- Owner: skills
- Requirements: SKL-004, SKL-003
- Dependencies: SKL-003
- Real boundary required: true
- Assertions:
  - **SKL-004-P01 [positive]** — Promote only evaluated versions into the registry with compatibility, thresholds, promotion state and rollback target; promotion is separate from candidate execution.
  - **SKL-004-N01 [negative]** — Let a skill attempt to mutate its own promotion/capability state and prove the runtime/registry denies the operation.
  - **SKL-004-R01 [recovery]** — Rollback an active skill version and verify new tasks resolve the prior qualified version while already-running tasks retain their admitted version identity.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SKL-005 — Implement task-scoped skill materialization
- Milestone: 8
- Owner: skills
- Requirements: SKL-005, SEC-001
- Dependencies: SKL-004, MAC-005
- Real boundary required: true
- Assertions:
  - **SKL-005-P01 [positive]** — Resolve only qualified task-required skills, materialize them into the target under the admitted capability snapshot, and record exact versions in run evidence.
  - **SKL-005-N01 [negative]** — Request an unqualified/incompatible skill or one requiring capability beyond the task snapshot and verify materialization is denied.
  - **SKL-005-R01 [recovery]** — After task/target teardown remove task-scoped skill materialization while durable registry/evidence remains intact.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BUS-001 — Implement Business Capability Pack contract
- Milestone: 9
- Owner: business
- Requirements: BUS-001
- Dependencies: GATE-M8
- Real boundary required: true
- Assertions:
  - **BUS-001-P01 [positive]** — Validate a pack containing identity/version, knowledge/skill/tool/connector requirements, RBAC, policy, approvals, workflows, I/O, evidence, evaluations, compatibility and lifecycle metadata.
  - **BUS-001-N01 [negative]** — Omit evaluation thresholds, required RBAC/policy binding or compatibility metadata and verify the pack cannot reach publishable state.
  - **BUS-001-R01 [recovery]** — Load a prior compatible pack version during rollback and preserve installed dependency/evidence identities.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BUS-002 — Implement capability compiler intake and semantic decomposition
- Milestone: 9
- Owner: business
- Requirements: BUS-002, BUS-003
- Dependencies: BUS-001, KNW-003
- Real boundary required: true
- Assertions:
  - **BUS-002-P01 [positive]** — Ingest authoritative enterprise material and produce a candidate compilation model separating entities, rules, permissions, procedures, inputs/outputs and evidence sources.
  - **BUS-002-N01 [negative]** — Feed contradictory or insufficiently authoritative material and verify the compiler emits explicit unresolved conflicts rather than inventing business rules.
  - **BUS-002-R01 [recovery]** — Update one source and recompile incrementally while preserving source-to-output provenance and invalidating affected candidate components.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BUS-003 — Implement process reconstruction and skill/workflow extraction
- Milestone: 9
- Owner: business
- Requirements: BUS-003
- Dependencies: BUS-002, SKL-004
- Real boundary required: true
- Assertions:
  - **BUS-003-P01 [positive]** — Reconstruct business steps, decisions, roles, approvals and failure paths, then bind reusable qualified skills and WorkGraph templates without creating a separate executor.
  - **BUS-003-N01 [negative]** — Generate a workflow requiring a permission/approval absent from source policy and verify compilation keeps it unresolved/unpublishable.
  - **BUS-003-R01 [recovery]** — Change a process dependency and regenerate only affected workflow/skill references while preserving stable identities for unaffected components.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BUS-004 — Bind tools, RBAC, policy and evidence to capability packs
- Milestone: 9
- Owner: business
- Requirements: BUS-003, BUS-005, EXT-001
- Dependencies: BUS-003, EXT-001
- Real boundary required: true
- Assertions:
  - **BUS-004-P01 [positive]** — Resolve every operation to a versioned ToolOperation, required capability, role/permission, policy/approval rule and evidence requirement without embedding credentials.
  - **BUS-004-N01 [negative]** — Attempt to bind a tool whose fidelity/effect class cannot meet the pack acceptance contract or whose required permission is unresolved; publication must fail.
  - **BUS-004-R01 [recovery]** — Rotate connector/tool version and re-run compatibility/evaluation before the pack can select the new binding.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## BUS-005 — Qualify and publish business capability packs
- Milestone: 9
- Owner: business
- Requirements: BUS-004, BUS-006
- Dependencies: BUS-004
- Real boundary required: true
- Assertions:
  - **BUS-005-P01 [positive]** — Execute declared evaluation cases through canonical runtime/effect/evidence paths and publish only when every mandatory threshold/dependency/support condition passes.
  - **BUS-005-N01 [negative]** — Force one high-risk negative evaluation to fail while aggregate score remains high and verify mandatory-case failure prevents publication.
  - **BUS-005-R01 [recovery]** — Rollback the published pack to its declared rollback target and verify new executions resolve the rollback version without corrupting historical run evidence.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## EXT-001 — Implement canonical Tool Registry and fidelity contract
- Milestone: 9
- Owner: tools
- Requirements: EXT-001
- Dependencies: GATE-M8
- Real boundary required: true
- Assertions:
  - **EXT-001-P01 [positive]** — Register each tool operation with schema/version, semantic effect class, fidelity class, capability/policy needs, timeout/idempotency and evidence contract.
  - **EXT-001-N01 [negative]** — Register a consequential operation as harmless or a degrading operation as lossless and verify registry/evaluation policy rejects the unsafe declaration.
  - **EXT-001-R01 [recovery]** — Deprecate an operation version and keep admitted running steps pinned while new admissions resolve only supported compatible versions.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## EXT-002 — Implement governed integration broker
- Milestone: 9
- Owner: connectors
- Requirements: EXT-002, SEC-004, EFF-001
- Dependencies: EXT-001, SEC-004, EFF-003
- Real boundary required: true
- Assertions:
  - **EXT-002-P01 [positive]** — Execute connector operations through credential handles, ToolOperation, policy/privacy/approval/effect mediation and return normalized receipts/evidence.
  - **EXT-002-N01 [negative]** — Invoke the connector adapter directly with reusable secret material or without EffectRecord for a consequential operation and prove the path is unreachable/rejected.
  - **EXT-002-R01 [recovery]** — On ambiguous connector timeout create UNKNOWN effect and reconcile using connector idempotency/provider state before retry.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## EXT-003 — Implement authenticated idempotent webhook ingress
- Milestone: 9
- Owner: connectors
- Requirements: EXT-003
- Dependencies: EXT-002, DAT-004
- Real boundary required: true
- Assertions:
  - **EXT-003-P01 [positive]** — Authenticate webhook source, normalize event identity, deduplicate delivery and correlate accepted ingress to tenant/tool/work initiation before creating work.
  - **EXT-003-N01 [negative]** — Replay the same webhook and submit one with invalid source authentication; duplicate must not create work and invalid source must be rejected.
  - **EXT-003-R01 [recovery]** — Crash after durable ingress record but before work creation and resume exactly once from the recorded webhook identity.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M9 — Milestone acceptance gate
- Milestone: 9
- Owner: release
- Requirements: INV-008
- Dependencies: BUS-001, BUS-002, BUS-003, BUS-004, BUS-005, EXT-001, EXT-002, EXT-003, GATE-M8
- Real boundary required: false
- Assertions:
  - **GATE-M9-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M9 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M9-N01 [negative]** — Remove or fail one blocking predecessor for milestone M9 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M9-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M9 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## AUT-001 — Implement timezone-aware logical scheduling
- Milestone: 10
- Owner: automation
- Requirements: AUT-001
- Dependencies: GATE-M9
- Real boundary required: true
- Assertions:
  - **AUT-001-P01 [positive]** — Persist timezone, local schedule rule, next-fire calculation and logical fire identity; test normal dates plus daylight-time gap/fold cases using explicit policy.
  - **AUT-001-N01 [negative]** — Create an ambiguous local-time schedule without a declared fold/gap rule and verify validation refuses activation.
  - **AUT-001-R01 [recovery]** — Restart scheduler across a clock transition and prove each logical occurrence has at most one accepted fire identity.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## AUT-002 — Implement missed-fire and bounded catch-up policy
- Milestone: 10
- Owner: automation
- Requirements: AUT-002
- Dependencies: AUT-001
- Real boundary required: true
- Assertions:
  - **AUT-002-P01 [positive]** — Implement SKIP, FIRE_ONCE and CATCH_UP_BOUNDED with an explicit maximum and durable history of logical occurrences.
  - **AUT-002-N01 [negative]** — Simulate prolonged outage producing more missed occurrences than the catch-up bound and verify excess work is not emitted silently.
  - **AUT-002-R01 [recovery]** — Recover scheduler after outage and prove emitted catch-up fires retain original logical identities and cannot duplicate on a second restart.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## AUT-003 — Re-evaluate authority on every automation fire
- Milestone: 10
- Owner: automation
- Requirements: AUT-003, SEC-001
- Dependencies: AUT-001, SEC-001
- Real boundary required: true
- Assertions:
  - **AUT-003-P01 [positive]** — At fire time resolve current support status, capability, policy, credential availability and target health before admitting the WorkGraph.
  - **AUT-003-N01 [negative]** — Revoke a permission after schedule creation but before fire and verify the fire is blocked/attention-required rather than using stale authority.
  - **AUT-003-R01 [recovery]** — Restore authority later and follow the configured missed-fire policy rather than replaying an unauthorized original execution.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## AUT-004 — Implement durable pause, resume and delete semantics
- Milestone: 10
- Owner: automation
- Requirements: AUT-004
- Dependencies: AUT-002, AUT-003
- Real boundary required: true
- Assertions:
  - **AUT-004-P01 [positive]** — Persist automation state transitions and serialize pause/resume/delete against scheduler claiming so a logical fire cannot race into duplicate execution.
  - **AUT-004-N01 [negative]** — Pause at the same instant as scheduler claim and prove exactly one defined outcome occurs according to transaction order.
  - **AUT-004-R01 [recovery]** — Restart scheduler after delete and prove deleted automation cannot reappear from stale cache/lease state.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## COL-001 — Implement collaboration as runtime projections
- Milestone: 10
- Owner: runtime
- Requirements: INV-006, RUN-004
- Dependencies: RUN-005, GATE-M9
- Real boundary required: true
- Assertions:
  - **COL-001-P01 [positive]** — Represent teammate rooms/groups/threads as participants and typed WorkGraph turn/message relations over canonical agents/runtime rather than a second scheduler.
  - **COL-001-N01 [negative]** — Attempt to add a collaboration-specific execution queue that can mutate task state independently and verify ownership/import checks reject it.
  - **COL-001-R01 [recovery]** — Restart collaboration clients while worker turns continue and rebuild the complete collaboration projection from canonical events/results.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## COL-002 — Implement durable typed handoff and message contracts
- Milestone: 10
- Owner: runtime
- Requirements: RUN-004, DAT-005
- Dependencies: COL-001
- Real boundary required: true
- Assertions:
  - **COL-002-P01 [positive]** — Persist handoff/message identity, sender, recipients, target turn/work item, payload/artifact refs, capability context and delivery outcome.
  - **COL-002-N01 [negative]** — Deliver the same handoff twice or target a cancelled/unauthorized worker and verify no duplicate work/admission occurs.
  - **COL-002-R01 [recovery]** — Recover after delivery interruption and either complete the same delivery once or expose a durable failed/cancelled outcome.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## COL-003 — Implement durable attention and notification delivery
- Milestone: 10
- Owner: notifications
- Requirements: RUN-008
- Dependencies: COL-002, DAT-004
- Real boundary required: true
- Assertions:
  - **COL-003-P01 [positive]** — Create notification/attention records from canonical events with recipient, channel class, urgency, expiry, deep-link target and delivery receipts without owning approval truth.
  - **COL-003-N01 [negative]** — Replay a notification delivery or acknowledge it from the wrong tenant and verify idempotent/tenant-safe behavior.
  - **COL-003-R01 [recovery]** — Recover notification service after outage and deliver eligible pending notifications without changing the underlying task/approval state.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## COL-004 — Implement persistent teammate routines
- Milestone: 10
- Owner: automation
- Requirements: AUT-003, RUN-002
- Dependencies: AUT-004, COL-001
- Real boundary required: true
- Assertions:
  - **COL-004-P01 [positive]** — Bind routines to persistent teammate identity and schedule/work templates while resolving current capabilities and workspace on each fire.
  - **COL-004-N01 [negative]** — Delete/disable the teammate before routine fire and verify no orphan routine starts under stale agent identity.
  - **COL-004-R01 [recovery]** — Restore service after missed routine windows and apply the routine missed-fire policy with durable logical-fire identities.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M10 — Milestone acceptance gate
- Milestone: 10
- Owner: release
- Requirements: INV-008
- Dependencies: AUT-001, AUT-002, AUT-003, AUT-004, COL-001, COL-002, COL-003, COL-004, GATE-M9
- Real boundary required: false
- Assertions:
  - **GATE-M10-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M10 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M10-N01 [negative]** — Remove or fail one blocking predecessor for milestone M10 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M10-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M10 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## GATE-M11 — Milestone acceptance gate
- Milestone: 11
- Owner: release
- Requirements: INV-008
- Dependencies: UX-001, UX-002, UX-003, UX-004, UX-005, UX-006, UX-007, UX-008, GATE-M10
- Real boundary required: false
- Assertions:
  - **GATE-M11-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M11 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M11-N01 [negative]** — Remove or fail one blocking predecessor for milestone M11 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M11-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M11 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## UX-001 — Implement desktop workbench shell and navigation
- Milestone: 11
- Owner: frontend
- Requirements: UX-001, INV-002, UX-006
- Dependencies: GATE-M10
- Real boundary required: true
- Assertions:
  - **UX-001-P01 [positive]** — Deliver a desktop workbench with teammate/task/research/capability/automation navigation, central canonical timeline, attention/evidence side panel and artifact/live-workspace pane.
  - **UX-001-N01 [negative]** — Disconnect the API/event stream and verify the shell shows explicit offline/degraded state without allowing local UI state to claim task completion.
  - **UX-001-R01 [recovery]** — Reconnect from the last durable cursor and rebuild visible state without duplicating messages, effects or approvals.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## UX-002 — Implement canonical event timeline and client convergence
- Milestone: 11
- Owner: frontend
- Requirements: UX-002
- Dependencies: UX-001, DAT-003
- Real boundary required: true
- Assertions:
  - **UX-002-P01 [positive]** — Apply snapshot plus ordered RuntimeEvent cursor to render run/worker/tool/model/effect/approval states consistently across two client instances.
  - **UX-002-N01 [negative]** — Inject duplicate and out-of-order delivery and verify clients converge to identical canonical projection without locally inventing sequence.
  - **UX-002-R01 [recovery]** — Clear local client cache, reload and prove the complete visible state reconstructs from server snapshot/events.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## UX-003 — Implement live browser/computer workspace pane
- Milestone: 11
- Owner: frontend
- Requirements: UX-004, BRW-002
- Dependencies: UX-001, BRW-004
- Real boundary required: true
- Assertions:
  - **UX-003-P01 [positive]** — Render the existing live session with observation state, target/session identity, viewer/controller lease and takeover/return controls without browser restart.
  - **UX-003-N01 [negative]** — Attempt control while another actor holds the controller lease and verify UI cannot send actuator commands as though it owned control.
  - **UX-003-R01 [recovery]** — Recover from pane/network disconnect and reattach to the same healthy session or expose explicit ended/degraded state.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## UX-004 — Implement exact-scope approval user experience
- Milestone: 11
- Owner: frontend
- Requirements: UX-003, EFF-002
- Dependencies: UX-002, EFF-002
- Real boundary required: true
- Assertions:
  - **UX-004-P01 [positive]** — Display operation, target, consequential arguments, data class, financial scope where applicable, reason and expiry from the canonical ApprovalRequest and submit the exact request identity.
  - **UX-004-N01 [negative]** — Change the underlying effect scope after UI render and prove approval submission is rejected or refreshed rather than authorizing hidden changed arguments.
  - **UX-004-R01 [recovery]** — Resolve approval on another authorized client and update the first client from canonical events without a second approval action.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## UX-005 — Implement artifact and evidence exploration
- Milestone: 11
- Owner: frontend
- Requirements: UX-001, DAT-006
- Dependencies: UX-002, DAT-006
- Real boundary required: true
- Assertions:
  - **UX-005-P01 [positive]** — List and open task artifacts/evidence using server grants, showing provenance, digest, producer, scan/freshness status and related claim/effect/run identities.
  - **UX-005-N01 [negative]** — Attempt to open an artifact from another tenant or expired grant and verify no bytes/metadata beyond permitted denial context are exposed.
  - **UX-005-R01 [recovery]** — Refresh after object-service interruption and restore artifact view from canonical metadata without claiming unavailable bytes were verified.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## UX-006 — Implement web client on canonical commands and events
- Milestone: 11
- Owner: frontend
- Requirements: UX-005, INV-002
- Dependencies: UX-002
- Real boundary required: true
- Assertions:
  - **UX-006-P01 [positive]** — Run the web surface against the same command/event contracts as desktop and demonstrate cross-client convergence for task, approval and research states.
  - **UX-006-N01 [negative]** — Add a web-only local task mutation and verify client architecture/import tests reject shadow authority.
  - **UX-006-R01 [recovery]** — Reconnect web after offline period and catch up from cursor without restarting server-side work.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## UX-007 — Implement mobile attention and continuation client
- Milestone: 11
- Owner: frontend
- Requirements: UX-005, RUN-008
- Dependencies: UX-002, COL-003
- Real boundary required: true
- Assertions:
  - **UX-007-P01 [positive]** — Implement mobile task status, notifications, approval, questions and supported handoff/takeover surfaces using canonical APIs/events only.
  - **UX-007-N01 [negative]** — Attempt an unsupported machine/effect action from mobile and verify capability/support gating hides or rejects the action rather than approximating it locally.
  - **UX-007-R01 [recovery]** — Resume a task viewed on another client and prove mobile state converges from server without changing execution ownership.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## UX-008 — Implement packaged command-line client
- Milestone: 11
- Owner: frontend
- Requirements: UX-005, INV-002
- Dependencies: UX-002
- Real boundary required: true
- Assertions:
  - **UX-008-P01 [positive]** — Provide authenticated commands for task start/status/cancel, approval response, artifact/evidence lookup and event follow using canonical schemas.
  - **UX-008-N01 [negative]** — Attempt to invoke a local model/runtime/effect shortcut from the CLI and verify the package contains no alternate execution authority.
  - **UX-008-R01 [recovery]** — Interrupt event follow and resume from stored cursor, receiving only missing canonical events.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M12 — Milestone acceptance gate
- Milestone: 12
- Owner: release
- Requirements: INV-008
- Dependencies: SEC-006, SEC-007, SRE-001, SRE-002, SRE-003, SRE-004, SRE-005, SRE-006, GATE-M11
- Real boundary required: false
- Assertions:
  - **GATE-M12-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M12 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M12-N01 [negative]** — Remove or fail one blocking predecessor for milestone M12 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M12-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M12 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## SEC-006 — Run cross-tenant adversarial qualification
- Milestone: 12
- Owner: security
- Requirements: SEC-006
- Dependencies: SRE-003, DAT-008, MAC-008
- Real boundary required: true
- Assertions:
  - **SEC-006-P01 [positive]** — Probe APIs, events, artifacts, model context, connectors, workers, machines and client cursors for cross-tenant isolation using distinct tenant fixtures.
  - **SEC-006-N01 [negative]** — Attempt identifier substitution, stale grant reuse and cursor replay across tenants and require denial before protected data/effect execution.
  - **SEC-006-R01 [recovery]** — Repeat probes after database/cache/service failover to prove recovery paths preserve tenant enforcement.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SEC-007 — Qualify build and artifact provenance
- Milestone: 12
- Owner: release
- Requirements: SEC-008
- Dependencies: GOV-004, SRE-005
- Real boundary required: true
- Assertions:
  - **SEC-007-P01 [positive]** — Bind qualified source commit, dependency locks, generated bindings, service/client artifacts, container/image/config digests and migrations into a reproducible candidate input set.
  - **SEC-007-N01 [negative]** — Substitute one artifact while retaining its filename or use generated bindings from another commit and prove provenance validation fails.
  - **SEC-007-R01 [recovery]** — Rebuild from the same qualified inputs and compare declared reproducibility fields; any permitted nondeterminism must be explicitly identified and excluded from semantic identity.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SRE-001 — Implement end-to-end telemetry correlation
- Milestone: 12
- Owner: sre
- Requirements: SRE-001
- Dependencies: GATE-M11
- Real boundary required: true
- Assertions:
  - **SRE-001-P01 [positive]** — Correlate command, session, run, step, model request, tool operation, effect, worker, target and recovery identities across logs, metrics and traces without leaking protected content.
  - **SRE-001-N01 [negative]** — Remove run/effect correlation from one service boundary and verify observability conformance fails the trace completeness check.
  - **SRE-001-R01 [recovery]** — Restart telemetry backend and ensure product execution continues with bounded buffering/degradation while missing telemetry is explicitly measurable.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SRE-002 — Implement SLI and SLO measurement
- Milestone: 12
- Owner: sre
- Requirements: SRE-001, SRE-004, SRE-005
- Dependencies: SRE-001
- Real boundary required: true
- Assertions:
  - **SRE-002-P01 [positive]** — Measure authenticated command/event availability, admission latency, event projection lag and machine readiness using production-like probes and declared exclusion rules.
  - **SRE-002-N01 [negative]** — Hide failed requests behind retries or exclude an unregistered failure class and verify SLO calculation tests reject the manipulated measurement.
  - **SRE-002-R01 [recovery]** — Recover metrics pipeline from outage and preserve the outage as missing/failed observation rather than backfilling artificial success.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SRE-003 — Implement RecoveryConsistencyPoint
- Milestone: 12
- Owner: sre
- Requirements: SRE-003, EFF-003
- Dependencies: SRE-001, MAC-007, EFF-003
- Real boundary required: true
- Assertions:
  - **SRE-003-P01 [positive]** — Create a recovery point binding database commit position, canonical event sequence, evidence manifest digest, snapshot inventory digest, effect-settlement watermark and unresolved UNKNOWN effect IDs.
  - **SRE-003-N01 [negative]** — Attempt to declare recovery consistent using database restore alone while referenced evidence/snapshot/effect watermark differs; verification must fail.
  - **SRE-003-R01 [recovery]** — Restore all bound components to a compatible recovery point and reconcile UNKNOWN effects before reopening consequential execution.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SRE-004 — Qualify backup and restore objectives
- Milestone: 12
- Owner: sre
- Requirements: SRE-002, SRE-003
- Dependencies: SRE-003
- Real boundary required: true
- Assertions:
  - **SRE-004-P01 [positive]** — Execute destructive restore drills demonstrating authoritative-state RPO <=300s/RTO <=1800s and evidence/object RPO <=900s/RTO <=3600s.
  - **SRE-004-N01 [negative]** — Provide a restore report missing one RecoveryConsistencyPoint component and verify DR qualification fails despite database availability.
  - **SRE-004-R01 [recovery]** — After restore, replay/reconcile to current safe state and prove committed effects are not duplicated.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SRE-005 — Qualify load, soak and degradation behavior
- Milestone: 12
- Owner: quality
- Requirements: SRE-006, SRE-004, SRE-005
- Dependencies: SRE-002
- Real boundary required: true
- Assertions:
  - **SRE-005-P01 [positive]** — Run sustained concurrent task/model/research/event load and demonstrate declared latency/readiness objectives without unbounded queues or tenant starvation.
  - **SRE-005-N01 [negative]** — Overload one dependency and verify bounded admission/backpressure/degradation rather than silent drops, uncontrolled retries or cross-tenant resource theft.
  - **SRE-005-R01 [recovery]** — Return dependency capacity and prove queues/reservations settle without a retry storm or duplicate effect execution.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## SRE-006 — Implement tenant quota and cost controls
- Milestone: 12
- Owner: sre
- Requirements: SRE-006, RUN-006
- Dependencies: RUN-007, SRE-001
- Real boundary required: true
- Assertions:
  - **SRE-006-P01 [positive]** — Enforce per-tenant budgets/quotas for model, research fan-out, workers, storage and connector usage with auditable reservation/settlement.
  - **SRE-006-N01 [negative]** — Race two tenants against a shared capacity limit and prove one tenant cannot consume another tenant’s reserved budget/quota.
  - **SRE-006-R01 [recovery]** — Recover quota service after restart from authoritative reservations/settlements without resetting spend counters.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M13 — Milestone acceptance gate
- Milestone: 13
- Owner: release
- Requirements: INV-008
- Dependencies: QA-001, QA-002, QA-003, QA-004, QA-005, QA-006, QA-007, QA-008, GATE-M12
- Real boundary required: false
- Assertions:
  - **GATE-M13-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M13 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M13-N01 [negative]** — Remove or fail one blocking predecessor for milestone M13 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M13-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M13 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## QA-001 — Qualify persistent teammate and worker vertical
- Milestone: 13
- Owner: quality
- Requirements: RUN-008, RUN-004
- Dependencies: GATE-M12
- Real boundary required: true
- Assertions:
  - **QA-001-P01 [positive]** — Run persistent teammate work with at least 32 asynchronous workers, client disconnect, partial results, cancellation and restart while preserving canonical graph/event identities.
  - **QA-001-N01 [negative]** — Inject duplicate worker results and stale client commands; verify no duplicate work/effects and canonical projection remains consistent.
  - **QA-001-R01 [recovery]** — Kill client/runtime processes during active work, restart and complete from durable state without replaying committed effects.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## QA-002 — Qualify model gateway vertical
- Milestone: 13
- Owner: quality
- Requirements: MOD-007, MOD-005, MOD-006
- Dependencies: GATE-M12, MOD-008
- Real boundary required: true
- Assertions:
  - **QA-002-P01 [positive]** — Execute enabled model profile through routing, privacy, streaming, cancellation, usage reservation/settlement and failover under real boundary conditions.
  - **QA-002-N01 [negative]** — Attempt direct provider access and protected egress denial case; direct path must be unreachable and denied payload must emit zero protected bytes.
  - **QA-002-R01 [recovery]** — Restart gateway during settling usage and complete idempotent late settlement without double charge.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## QA-003 — Qualify evidence-first research vertical
- Milestone: 13
- Owner: quality
- Requirements: CTX-006
- Dependencies: GATE-M12, CTX-008
- Real boundary required: true
- Assertions:
  - **QA-003-P01 [positive]** — Run the sealed wide/deep benchmark through SearchProgram and meet every declared recall/precision/citation/freshness/duplicate/completion threshold.
  - **QA-003-N01 [negative]** — Alter a cited claim or scorer identity after run and verify independent verification or benchmark binding rejects the result.
  - **QA-003-R01 [recovery]** — Resume an interrupted benchmark from durable intermediate state and reproduce final scoring within declared tolerance.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## QA-004 — Qualify protected and financial effect vertical
- Milestone: 13
- Owner: quality
- Requirements: EFF-005, EFF-006, EFF-003
- Dependencies: GATE-M12, EFF-003, BRW-003
- Real boundary required: true
- Assertions:
  - **QA-004-P01 [positive]** — Execute approval-bound message/publication/financial effects and verify exact semantic scope, policy, Effect Ledger, receipt and evidence.
  - **QA-004-N01 [negative]** — Change financial amount by one minor unit, change payee, or disguise a consequential browser submit as generic input; all must be denied before actuator/provider call.
  - **QA-004-R01 [recovery]** — Force ambiguous timeout, restart effect worker, reconcile UNKNOWN and prove at-most-once consequential outcome.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## QA-005 — Qualify machine, browser and endpoint vertical
- Milestone: 13
- Owner: quality
- Requirements: MAC-007, BRW-006
- Dependencies: GATE-M12, BRW-008, MAC-008
- Real boundary required: true
- Assertions:
  - **QA-005-P01 [positive]** — Provision isolated and persistent targets, execute typed guest/browser actions, human takeover, endpoint relay, checkpoint/restore and stale-generation fencing.
  - **QA-005-N01 [negative]** — Replay old fence/generation after restore and attempt unqualified support target; both must be blocked before actuation.
  - **QA-005-R01 [recovery]** — Disconnect worker/browser/client surfaces, restore service and prove safe reconnect/redelivery without duplicate effect.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## QA-006 — Qualify skill and business capability vertical
- Milestone: 13
- Owner: quality
- Requirements: SKL-002, BUS-004, BUS-005
- Dependencies: GATE-M12, BUS-005, SKL-005
- Real boundary required: true
- Assertions:
  - **QA-006-P01 [positive]** — Ingest authoritative material, evaluate/promote a skill, compile/evaluate/publish a Business Capability Pack and execute it through canonical runtime/tools/effects/evidence.
  - **QA-006-N01 [negative]** — Inject an authority-expanding skill or capability with unresolved RBAC/tool fidelity and prove promotion/publication fails.
  - **QA-006-R01 [recovery]** — Rollback skill and capability versions and verify new work resolves rollback targets while historical run evidence remains version-pinned.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## QA-007 — Qualify automation and multi-client convergence
- Milestone: 13
- Owner: quality
- Requirements: AUT-004, UX-002
- Dependencies: GATE-M12, AUT-004, UX-008
- Real boundary required: true
- Assertions:
  - **QA-007-P01 [positive]** — Exercise timezone/DST/missed-fire routines while desktop, web, mobile and CLI observe/respond to the same task/approval event stream.
  - **QA-007-N01 [negative]** — Inject duplicate logical fire and out-of-order client events; verify one work admission and convergent client projections.
  - **QA-007-R01 [recovery]** — Restart scheduler and all clients, then resume from canonical fire history/event cursors without duplicate work.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## QA-008 — Qualify disaster recovery and effect consistency
- Milestone: 13
- Owner: quality
- Requirements: SRE-002, SRE-003, EFF-004
- Dependencies: GATE-M12, SRE-004
- Real boundary required: true
- Assertions:
  - **QA-008-P01 [positive]** — Perform production-like recovery using a RecoveryConsistencyPoint and meet declared RPO/RTO while preserving event/artifact/snapshot/effect consistency.
  - **QA-008-N01 [negative]** — Restore database to a point inconsistent with effect/evidence watermark and prove the system refuses production reopen.
  - **QA-008-R01 [recovery]** — Complete reconciliation after restore and verify no committed external effect is replayed and unresolved UNKNOWN effects are handled before new consequential work.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## GATE-M14 — Production readiness gate
- Milestone: 14
- Owner: release
- Requirements: INV-008, REL-005
- Dependencies: REL-001, REL-002, REL-003, REL-004, REL-005, REL-006, REL-007, GATE-M13
- Real boundary required: false
- Assertions:
  - **GATE-M14-P01 [positive]** — Confirm every blocking task and mapped qualification prerequisite for milestone M14 has valid completion evidence bound to the current implementation artifacts.
  - **GATE-M14-N01 [negative]** — Remove or fail one blocking predecessor for milestone M14 and verify the gate refuses advancement with the exact missing task/assertion identified.
  - **GATE-M14-R01 [recovery]** — After restoring valid evidence for the failed predecessor, re-evaluate milestone M14 deterministically without changing other completed task evidence.
- Required evidence: predecessor_evidence_index, gate_report, repository_commit, artifact_digests
- Forbidden shortcuts: manual_override, mock_as_acceptance, ignored_blocking_failure

## REL-001 — Create immutable release candidate
- Milestone: 14
- Owner: release
- Requirements: REL-001, SEC-008, REL-002
- Dependencies: GATE-M13
- Real boundary required: true
- Assertions:
  - **REL-001-P01 [positive]** — Create a candidate identity binding exact source commit, generated bindings, service/client artifacts, images/configuration, migrations and support selection.
  - **REL-001-N01 [negative]** — Change any bound artifact/config/source after candidate creation and verify the modified set has a different candidate identity and cannot reuse prior qualification.
  - **REL-001-R01 [recovery]** — Re-materialize the candidate from stored artifact identities and verify every digest/config/migration matches before qualification begins.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## REL-002 — Qualify exact release candidate
- Milestone: 14
- Owner: release
- Requirements: REL-003
- Dependencies: REL-001
- Real boundary required: true
- Assertions:
  - **REL-002-P01 [positive]** — Run every blocking suite mapped to enabled support profiles against the exact candidate and record candidate-bound reports with all blocking assertions PASS.
  - **REL-002-N01 [negative]** — Substitute a report from another candidate or omit one mapped suite and verify candidate cannot become CANDIDATE_QUALIFIED.
  - **REL-002-R01 [recovery]** — Resume interrupted qualification without rebuilding candidate and retain completed suite evidence only when candidate/config identities still match.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## REL-003 — Deploy qualified candidate to canary
- Milestone: 14
- Owner: release
- Requirements: REL-004
- Dependencies: REL-002
- Real boundary required: true
- Assertions:
  - **REL-003-P01 [positive]** — Deploy the exact CANDIDATE_QUALIFIED artifacts/config/migrations to canary and record deployment identity, cohort, health and post-deploy checks.
  - **REL-003-N01 [negative]** — Attempt canary using rebuilt/unqualified artifact or unsupported enabled profile and verify deployment gate refuses promotion.
  - **REL-003-R01 [recovery]** — Recover a failed canary deployment by executing the declared rollback without altering the candidate evidence record.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## REL-004 — Prove canary rollback and data/effect compatibility
- Milestone: 14
- Owner: release
- Requirements: REL-004
- Dependencies: REL-003
- Real boundary required: true
- Assertions:
  - **REL-004-P01 [positive]** — Execute rollback from canary under live representative traffic and prove schema/data/effect compatibility, no duplicate effects and restored service health.
  - **REL-004-N01 [negative]** — Introduce an irreversible migration without declared expand/contract rollback path and verify rollback qualification fails before GO decision.
  - **REL-004-R01 [recovery]** — After rollback restore canary to the same qualified candidate and rerun post-deploy checks without changing candidate identity.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## REL-005 — Record independent go or no-go decision
- Milestone: 14
- Owner: release
- Requirements: REL-003
- Dependencies: REL-004
- Real boundary required: true
- Assertions:
  - **REL-005-P01 [positive]** — Evaluate exact candidate suite results, SLO/security/DR/canary/rollback evidence and support selection into an explicit GO_APPROVED or NO_GO decision.
  - **REL-005-N01 [negative]** — Force one blocking suite/report to FAIL after aggregation and verify GO_APPROVED becomes invalid rather than relying on aggregate majority.
  - **REL-005-R01 [recovery]** — Re-evaluate after a corrected new candidate; prior decision remains immutable and cannot be reassigned to the new candidate.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## REL-006 — Seal readiness evidence bundle
- Milestone: 14
- Owner: release
- Requirements: REL-001, REL-003
- Dependencies: REL-005
- Real boundary required: true
- Assertions:
  - **REL-006-P01 [positive]** — Create a digest-bound readiness bundle containing candidate identity, all blocking reports, support selection, canary, rollback, SLO/security/DR results and GO decision; state becomes READINESS_EVIDENCE_SEALED only.
  - **REL-006-N01 [negative]** — Remove or substitute one blocking report after bundle creation and verify bundle integrity/readiness validation fails.
  - **REL-006-R01 [recovery]** — Reconstruct the bundle from immutable references and reproduce its digest without changing candidate release state.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## REL-007 — Enforce sole production-ready state owner
- Milestone: 14
- Owner: release
- Requirements: REL-005
- Dependencies: REL-006
- Real boundary required: true
- Assertions:
  - **REL-007-P01 [positive]** — Verify release-state policy allows only GATE-M14 to write PRODUCTION_READY after READINESS_EVIDENCE_SEALED and all gate dependencies pass.
  - **REL-007-N01 [negative]** — Attempt to have REL-006, a client, deployment script or administrator API write PRODUCTION_READY and verify state authority rejects it.
  - **REL-007-R01 [recovery]** — Restart release control after readiness seal and preserve state ownership rules before GATE-M14 evaluation.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion

## REL-008 — Promote the exact production-ready candidate
- Milestone: 15
- Owner: release
- Requirements: REL-006, REL-004
- Dependencies: GATE-M14
- Real boundary required: true
- Assertions:
  - **REL-008-P01 [positive]** — Promote exactly the candidate identified by the PRODUCTION_READY record without rebuilding, changing configuration, changing migrations or substituting artifacts.
  - **REL-008-N01 [negative]** — Attempt promotion with any artifact/configuration/source identity different from the production-ready candidate and verify promotion is rejected before deployment mutation.
  - **REL-008-R01 [recovery]** — If post-promotion verification fails, execute the declared production rollback while preserving immutable readiness, promotion and rollback evidence as distinct records.
- Required evidence: repository_commit, verification_report, assertion_results, artifact_digests, environment_identity, real_boundary_proof
- Forbidden shortcuts: mock_as_acceptance, hardcoded_success, placeholder_path, weakened_assertion


---

<!-- source: docs/21_WIRING.md -->

# 21 — Canonical wiring

## Command to outcome
`Client → quansio-api → quansio-control/auth-policy → quansio-runtime → Context/Model/Tool/Machine owners → RuntimeEvent → client projections`

## Model
`runtime → context projection → budget/privacy/routing → model-gateway → provider adapter → ModelEvent → runtime`

## Research
`runtime → context → SearchProgram → retrieval/index/browser tools → ResearchRecord/evidence → Context Projection/artifact`

## External effect
`runtime/tool proposal → capability → policy/privacy/sequence → approval if required → EffectRecord → integration-broker/browser/machine → receipt/evidence → reconciliation`

## Machine
`runtime → worker-gateway → machine-control lease/generation/fence → qworkerd → typed result/ACK → runtime`

## Business capability
`authoritative material → Capability Compiler → candidate pack → evaluation/publish → runtime resolution → normal WorkGraph/skills/tools/policy/effects/evidence`

## Notifications
`canonical attention event → quansio-notify → delivery receipt`; approval decisions still update control/effect authority, not notification state.

See `wiring/service-wiring.json` for machine-readable producer/consumer boundaries.


---

<!-- source: docs/22_DEPLOYMENT_AND_ENVIRONMENTS.md -->

# 22 — Deployment and environments

Minimum production-like qualification topology contains the authoritative relational store, durable event transport, cache/lease store, object/evidence storage, API/control/runtime, model gateway, context/indexer, worker gateway, machine control, integration broker, artifact/notification services and at least one enabled real execution/browser/model boundary.

Each environment has a stable environment identity, configuration digest, tenant-isolated test identities, health checks and teardown. Qualification never silently substitutes in-memory components for required durable boundaries.

Logical services can share a process during early build only when canonical interfaces/owners remain explicit and tests prove no direct cross-owner state mutation. Production deployment topology must be generated from registered deployables and support selection.

Secrets are provided through environment/secret management or brokered handles, not committed configuration. Provider credentials exist only in model-gateway scope; connector credentials remain behind integration-broker/broker scope.


---

<!-- source: docs/23_QUALIFICATION_MATRIX.md -->

# 23 — Qualification matrix

Blocking suites:

| Suite | Scope |
|---|---|
| Q-AUTH | authority, identity, tenant isolation |
| Q-DATA | durable storage, events, protocol state |
| Q-RUNTIME | graphs, workers, budgets, cancellation/recovery |
| Q-MODEL | server model fulfillment |
| Q-RESEARCH | evidence-first research thresholds |
| Q-EFFECT | policy, approvals, effects/reconciliation |
| Q-MACHINE | worker/machine fabric |
| Q-BROWSER | browser and endpoint control |
| Q-SKILL | knowledge and controlled skill evolution |
| Q-BUSINESS | capability compiler/packs |
| Q-AUTOMATION | schedules/collaboration |
| Q-CLIENT | supported client convergence/accessibility |
| Q-SECURITY | privacy, credentials, sequence guard, tenant isolation |
| Q-DR | recovery consistency, backup/restore |
| Q-LOAD | load, soak, quota, cost and degradation |
| Q-CANARY | candidate/canary/rollback/release |

Every enabled support profile maps to required suites and qualification tasks. Any blocking assertion failure is a suite failure regardless of aggregate pass percentage. Reports bind the exact code/config/environment/artifacts tested.


---

<!-- source: docs/24_RELEASE_AND_ROLLBACK.md -->

# 24 — Release, canary and rollback

```text
CANDIDATE_CREATED
      ↓
CANDIDATE_QUALIFIED
      ↓
CANARY_DEPLOYED
      ↓
CANARY_QUALIFIED
      ↓
GO_APPROVED
      ↓
READINESS_EVIDENCE_SEALED
      ↓
GATE-M14
      ↓
PRODUCTION_READY
      ↓
separate authorized promotion
      ↓
PRODUCTION_RELEASED
```

Only `GATE-M14` writes `PRODUCTION_READY`. `REL-006` only records `READINESS_EVIDENCE_SEALED`. A rebuild, source/config/migration/support-selection change creates a new candidate; qualification reports are candidate-bound and cannot be transferred.

Canary rollback is a blocking qualification activity. Database changes follow expand/contract or another explicitly reversible strategy. Rollback must preserve already committed external effect history and must never treat effect rollback as equivalent to infrastructure rollback.


---

<!-- source: docs/25_SUPPORT_MATRIX.md -->

# 25 — Support and qualification selection

Only three support states exist:
- `REQUIRED_GA`
- `DISABLED_UNTIL_QUALIFIED`
- `UNSUPPORTED`

A profile with implementation code but incomplete mapped qualification remains disabled. Support selection binds exact candidate/configuration plus all required suite reports.

Current canonical profiles are machine-readable in `registries/support-matrix.json`; categories include desktop/web/mobile/CLI clients, hosted isolated/persistent/local/private execution targets, managed browser, and primary/secondary model profiles. No unregistered profile may be advertised as supported.


---

<!-- source: docs/26_REAL_IMPLEMENTATION_COMPLETION_CONTRACT.md -->

# 26 — Real implementation completion contract

A task is complete only when production behavior exists on its canonical path and every blocking assertion has valid executed evidence.

## Not completion
- compiling interfaces or empty handlers
- UI without the backend/runtime path
- mocks/fakes replacing a required real boundary
- process-local state replacing required durable state
- simulated provider/connector success
- placeholder branches or swallowed exceptions returning success
- skipped/quarantined blocking tests
- hand-edited PASS state

## Evidence
Completion evidence binds exact task, requirements, task/requirement assertion IDs, repository identity, reachable commit, verification report digest/content, environment/configuration, artifact digests and real-boundary proof when required. Cryptographic report signatures are not required. The evidence validator independently reads and verifies the report/artifacts/repository rather than trusting an outer PASS label.

`BLOCKED_REAL_BOUNDARY` documents an unavailable dependency and exits non-success for closure. It records boundary, reason, owner, attempted verification and unblock condition.


---

<!-- source: docs/27_TEST_VERIFICATION_AND_EVIDENCE.md -->

# 27 — Test, verification and evidence matrix

Apply every relevant layer per task: unit, schema, contract, migration, integration, E2E, concurrency, duplicate/idempotency, cancellation, timeout, stale generation/capability, tenant isolation, approval-scope mutation, crash/restart, dependency outage, recovery, security/adversarial, load, DR, rollback and canary.

Real-boundary tasks must use the real class of boundary defined by their task/support profile. A fake can support isolated unit tests but cannot close real provider, browser, machine, durable-store or connector qualification.

## Report rules
- Report status PASS only when every blocking assertion result is PASS.
- Assertion IDs must exactly cover the task plus linked requirement assertion IDs.
- Commit must exist and be reachable from the configured protected qualification ref.
- Local artifact digests are re-hashed; remote artifacts require digest lookup or trusted build attestation receipt.
- If rollback/recovery is required, its assertion/result is blocking.
- Evidence validator has no authority to weaken task requirements.


---

<!-- source: docs/28_REPOSITORY_ADOPTION.md -->

# 28 — Repository adoption and implementation placement

Before implementing a task, inspect the current repository and classify relevant code as `ALREADY_COVERED`, `PARTIAL`, `GENUINE_GAP`, `CONFLICT`, `IMPLEMENTED_UNDOCUMENTED`; then choose disposition `REUSE_BEHIND_OWNER`, `MIGRATE`, `FREEZE_THEN_REMOVE`, `REMOVE_NOW`, or `BUILD`.

Reusable protocol translation/domain code may survive only behind the correct canonical owner. A reusable helper does not inherit architectural authority from its current location.

Do not create a new database, queue, browser stack, orchestrator, memory system or model/provider path because a task lacks an obvious home. Use the service ownership table and wiring first; if the requirement truly cannot fit a canonical owner, open an architecture decision rather than implementing a convenience subsystem.


---

<!-- source: docs/29_ARCHITECTURE_DIAGRAMS.md -->

# 29 — Architecture diagrams

Mermaid sources under `graphs/` are normative reading aids generated from the same architecture concepts as the wiring registry. They cover system architecture, runtime collaboration, research, machine fabric, business capability compilation and release state.

Diagrams never override schemas/registries. If a diagram and machine-readable source differ, generation/validation must fail and the diagram must be regenerated.


---

<!-- source: docs/30_PRODUCTION_READINESS_CHECKLIST.md -->

# 30 — Production readiness checklist

Production readiness requires all of the following for the exact candidate:

- canonical owner/import/source-completeness gates pass
- migrations and restore drills pass
- event/protocol replay and effect-aware recovery pass
- model gateway real-boundary qualification passes
- research quality thresholds pass
- privacy/RBAC/tenant isolation/adversarial suites pass
- approvals/effect/UNKNOWN reconciliation pass
- machine/browser/endpoint stale-generation and takeover tests pass
- skill and Business Capability promotion/rollback tests pass
- automation DST/missed-fire/duplicate-fire tests pass
- desktop/web/CLI and enabled mobile client convergence/accessibility pass
- load/SLO/quota/degradation tests pass
- DR RPO/RTO and RecoveryConsistencyPoint pass
- enabled support profiles have all mapped suites
- immutable candidate canary and rollback pass
- readiness evidence bundle is complete
- GATE-M14 alone transitions the candidate to PRODUCTION_READY


---

<!-- source: docs/31_CURRENT_REPOSITORY_IMPLEMENTATION_MAP.md -->

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
| indexer owner | CANONICAL (implemented) | `quansio/indexer` (ingest/chunk/freshness/tombstone/rebuild) exposed by the `quansio-indexer` service HTTP surface (`quansio/indexer/app.py`). |
| worker gateway | CANONICAL (implemented) | `quansio/worker_gateway` (governed transfers, endpoint relay, browser sessions/observations) exposed by the `quansio-worker-gateway` service (`quansio/worker_gateway/app.py`). |
| machine control | CANONICAL (implemented) | `quansio/machine_control` (inventory, placement/lease/fence, durable deliveries, isolated task runtimes, workspace computers, checkpoints, private targets) exposed by the `quansio-machine-control` service (`quansio/machine_control/app.py`). |
| artifact service | CANONICAL (implemented) | `quansio/artifact` (digest-addressed immutable store over MinIO + PostgreSQL metadata, scan states, restore verification) exposed by the `quansio-artifact` service (`quansio/artifact/app.py`). |
| notification service | CANONICAL (implemented) | `quansio/notify` (durable attention delivery, receipts, outage recovery) exposed by the `quansio-notify` service (`quansio/notify/app.py`). |
| integration broker | CANONICAL (implemented) | `quansio/integration_broker` (mediated connector operations over credential handles + authorized EffectRecords, HMAC webhook ingress with exactly-once work resume) exposed by the `quansio-integration-broker` service (`quansio/integration_broker/app.py`). The Tool Registry remains control-owned (`quansio/control/connectors.py`). |
| desktop/mobile/CLI supported clients | CANONICAL (implemented as thin projections) | `clients/cli` (packaged `quansio` CLI over canonical APIs), `clients/web` (chat-first canonical command/event projection; browser-qualified), `clients/desktop` (Electron shell around the web projection; provenance-verified binary, launch-qualified — stable process tree, no crash; window-content inspection requires macOS assistive/screen-recording access), `clients/mobile` (attention/continuation PWA; browser-qualified against live services). Shared convergence engine in `clients/pyapp`. Clients own no execution/task/model authority; acceptance: `tests/uxclients`, `tests/services`, browser qualification transcripts. |

Before deleting or moving any current path, identify active consumers, data compatibility, rollback and the task that proves canonical replacement. The final architecture gate must prove no conflicting production path remains reachable.


---

<!-- source: docs/32_AGENT_IMPLEMENTATION_PLAYBOOK.md -->

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


---

<!-- source: docs/33_API_SURFACE.md -->

# 33 — Canonical API surface

The exact transport can be HTTP/streaming RPC as generated by implementation, but semantic command ownership is fixed.

## Public command families
- `session/*`: authenticate, refresh, close, current identity
- `agents/*`: create/read/update allowed profile, activate/deactivate persistent teammate
- `work/*`: create work, status, cancel, wait/question response, event cursor
- `approvals/*`: list/read/respond to canonical ApprovalRequest
- `artifacts/*`: initiate upload, finalize digest, grant/read metadata/download
- `research/*`: start/query program, list ResearchRecords/evidence
- `capabilities/*`: browse/install qualified Business Capability Pack; compile/evaluate under authorized admin flows
- `skills/*`: browse qualified versions; candidate/evaluation/promotion only for authorized control flows
- `automations/*`: create/pause/resume/delete/list schedule and fire history
- `browser/*`: observe session, request/release controller, authorized action command
- `machines/*`: user/admin-visible target status; lifecycle commands are policy constrained
- `notifications/*`: list/ack attention
- `support/*`: read enabled/disabled profile status and qualification reason

## Streaming
Clients subscribe by tenant/workspace/run plus canonical cursor. Server returns ordered RuntimeEvent projections. Client ACK/cursor optimization does not delete canonical events.

## Error contract
Errors carry stable code, retryability, operation/request identity, policy/approval reference when relevant, and safe human message. Never expose secret/provider credentials in error text.


---

<!-- source: docs/34_REQUIREMENT_REGISTRY.md -->

# 34 — Normative requirements

| Requirement | Domain | Assertion | Normative statement | Linked tasks |
|---|---|---|---|---|
| AUT-001 | automation | AUT-001-A01 | Automation schedules use explicit timezone and logical fire identity and define DST gap/fold behavior. | AUT-001 |
| AUT-002 | automation | AUT-002-A01 | Missed-fire behavior is one of SKIP, FIRE_ONCE or CATCH_UP_BOUNDED with an explicit maximum catch-up count. | AUT-002 |
| AUT-003 | automation | AUT-003-A01 | Every automation fire re-evaluates current capability, policy, support and environment rather than reusing stale authority. | AUT-003, COL-004 |
| AUT-004 | automation | AUT-004-A01 | Pause, resume, delete and scheduler restart are durable and cannot create duplicate logical fires. | AUT-004, QA-007 |
| BRW-001 | browser | BRW-001-A01 | The managed browser exposes structured control and observation and uses visual interpretation only when structural state is insufficient. | BRW-001, BRW-002 |
| BRW-002 | browser | BRW-002-A01 | Browser sessions have durable identity and can be observed, taken over and returned without restarting the session. | BRW-001, BRW-004, BRW-008, UX-003 |
| BRW-003 | browser | BRW-003-A01 | Downloads, uploads and file transfers use artifact grants and evidence rather than unscoped host paths. | BRW-003, BRW-005 |
| BRW-004 | browser | BRW-004-A01 | Personal endpoint relay validates generation, lease, fence, capability, policy, effect, idempotency and approval binding before actuation. | BRW-006 |
| BRW-005 | browser | BRW-005-A01 | Browser/computer observations are correlated to step, target and evidence identities and can be replayed as observations without replaying effects. | BRW-007 |
| BRW-006 | browser | BRW-006-A01 | Every enabled browser or endpoint profile passes real navigation, structured action, consequential action, takeover, reconnect and stale-action qualification. | BRW-008, QA-005 |
| BUS-001 | business | BUS-001-A01 | Business Capability Pack is a versioned composition of knowledge, skills, tools, connectors, RBAC, policy, approvals, workflow templates, I/O, evidence, evaluations and compatibility. | BUS-001 |
| BUS-002 | business | BUS-002-A01 | Capability Compiler is an authoring/compilation pipeline and does not become a separate runtime or durable execution authority. | BUS-002 |
| BUS-003 | business | BUS-003-A01 | Capability compilation reconstructs business process and binds tools, policies, RBAC and evidence without embedding credentials. | BUS-002, BUS-003, BUS-004 |
| BUS-004 | business | BUS-004-A01 | A capability pack cannot publish until its dependencies resolve and its evaluation cases meet declared thresholds. | BUS-005, QA-006 |
| BUS-005 | business | BUS-005-A01 | Installed capability packs execute exclusively through canonical WorkGraph, tools, policy, effect, evidence and recovery paths. | BUS-004, QA-006 |
| BUS-006 | business | BUS-006-A01 | Capability compatibility, migration, deprecation and rollback are versioned and testable across pack updates. | BUS-005 |
| CTX-001 | research | CTX-001-A01 | SearchProgram is a typed bounded program over canonical research operators; arbitrary executable expressions are forbidden. | CTX-001 |
| CTX-002 | research | CTX-002-A01 | Research retrieval tracks source identity, freshness, provenance, access outcome and deduplication identity. | CTX-002, CTX-007 |
| CTX-003 | research | CTX-003-A01 | ResearchRecord separates entity identity, attributes, claims, sources, freshness, confidence and verification outcome. | CTX-003 |
| CTX-004 | research | CTX-004-A01 | Wide/deep research supports bounded fan-out, durable intermediate state, entity resolution, joins and independently verifiable evidence. | CTX-004 |
| CTX-005 | research | CTX-005-A01 | Claim verification can independently refetch cited sources and distinguish supported, unsupported, inaccessible and stale evidence. | CTX-005 |
| CTX-006 | research | CTX-006-A01 | Research qualification uses sealed dataset/source-policy/scorer identities and reproducible metric formulas with explicit thresholds. | CTX-008, QA-003 |
| CTX-007 | context | CTX-007-A01 | Context Projection is bounded, task-scoped, capability-aware and separately versioned from canonical history and durable knowledge. | CTX-006 |
| DAT-001 | data | DAT-001-A01 | Authentication establishes durable tenant, user, workspace and session identity before commands enter canonical services. | DAT-001 |
| DAT-002 | data | DAT-002-A01 | Authoritative relational state is migration-managed, tenant-scoped, transactionally consistent and restorable. | DAT-002, DAT-007, DAT-008, ENV-001 |
| DAT-003 | data | DAT-003-A01 | RuntimeEvent provides canonical ordered replay with stable event identity, producer identity, sequence, causality and execution generation. | DAT-003 |
| DAT-004 | data | DAT-004-A01 | Transactional outbox delivery cannot publish an event that is absent from committed authoritative state and remains idempotent after crashes. | DAT-004 |
| DAT-005 | data | DAT-005-A01 | Protocol state persists tool calls, approvals, questions, worker lifecycle, browser/computer control, waits and cancellation required for exact resume. | COL-002, DAT-005 |
| DAT-006 | data | DAT-006-A01 | Artifacts and evidence are immutable by digest, tenant-scoped, scanned where applicable and lifecycle-managed independently of task memory. | BRW-005, BRW-007, DAT-006, UX-005 |
| EFF-001 | effects | EFF-001-A01 | Every consequential semantic ToolOperation creates or references an EffectRecord before actuation. | EFF-001, EXT-002 |
| EFF-002 | effects | EFF-002-A01 | Approval receipts bind exact semantic scope and cannot authorize changed payee, amount, target, arguments or effect identity. | EFF-002, UX-004 |
| EFF-003 | effects | EFF-003-A01 | Ambiguous external timeouts enter UNKNOWN and reconcile provider/target state before any retry. | EFF-003, QA-004, SRE-003 |
| EFF-004 | effects | EFF-004-A01 | Committed effects are immutable history and are not replayed by reconnect, retry, graph recovery or client refresh. | EFF-001, QA-008, RUN-006 |
| EFF-005 | effects | EFF-005-A01 | Financial effects bind payee, amount in minor units, currency, purpose, funding handle, per-effect ceiling, cumulative budget and expiry. | EFF-002, QA-004 |
| EFF-006 | effects | EFF-006-A01 | Low-level browser/computer primitives are classified by semantic outcome before consequential actuation. | BRW-003, QA-004 |
| EFF-007 | effects | EFF-007-A01 | Effect receipts, failure outcomes and reconciliation evidence are durable and traceable to command, run, step and policy decision. | EFF-003 |
| EXT-001 | tools | EXT-001-A01 | Every tool operation has a canonical typed contract, semantic effect class, fidelity classification, required capability and version. | BUS-004, EXT-001 |
| EXT-002 | tools | EXT-002-A01 | Connector execution is mediated by the integration broker and cannot bypass capability, policy, privacy, approval or effect controls. | EXT-002 |
| EXT-003 | tools | EXT-003-A01 | Webhook ingress authenticates source, deduplicates delivery and records canonical correlation before creating work. | EXT-003 |
| GOV-001 | governance | GOV-001-A01 | Repository adoption records canonical ownership, existing-path disposition, durable stores, deployment entrypoints and duplicate authority before feature implementation. | GOV-001, GOV-002 |
| GOV-002 | governance | GOV-002-A01 | Authority generation is deterministic: canonical registries generate reading views, task graphs, counts and integrity metadata without hand-maintained duplicates. | GOV-003, GOV-004 |
| GOV-003 | governance | GOV-003-A01 | Production-source inspection rejects reachable incomplete implementation patterns while keeping tests, fixtures, generated output and vendor code separately scoped. | GOV-005 |
| GOV-004 | governance | GOV-004-A01 | Completion evidence is reproducible and binds actual repository commit, report, assertions, environment and artifacts; cryptographic report signatures are not required. | ENV-001, GOV-006 |
| GOV-005 | governance | GOV-005-A01 | Architecture decisions and threat-model changes record owner, context, decision, alternatives, affected invariants, migration/rollback impact and review trigger. | GOV-007 |
| INV-001 | architecture | INV-001-A01 | Every runtime state transition is owned by the canonical graph/runtime path; feature code may not create parallel orchestration authority. | GOV-002, RUN-001 |
| INV-002 | architecture | INV-002-A01 | Clients are command and projection surfaces and must reconstruct truth from canonical server state after reconnect. | UX-001, UX-006, UX-008 |
| INV-003 | architecture | INV-003-A01 | Memory and learned knowledge are not recovery mechanisms; recovery uses canonical events, protocol state, checkpoints, generations and effect reconciliation. | CTX-006, DAT-005, KNW-003 |
| INV-004 | architecture | INV-004-A01 | All consequential external actions use one semantic effect path before actuation. | GOV-007 |
| INV-005 | architecture | INV-005-A01 | All model-provider fulfillment occurs through the server-side model gateway; provider credentials are never delegated to clients, guests, tools, skills or connectors. | MOD-001 |
| INV-006 | architecture | INV-006-A01 | Persistent teammates, research, business capabilities, skills, automation and computer use compose over the same canonical primitives rather than feature-specific runtimes. | COL-001, GOV-002, GOV-007 |
| INV-007 | architecture | INV-007-A01 | Every durable mutable record has one owner, versioned schema, migration path, tenant boundary and recovery contract. | DAT-002, DAT-007, GOV-001, GOV-003 |
| INV-008 | architecture | INV-008-A01 | No production acceptance may be satisfied by a mock, placeholder, simulated success, hard-coded success or unexecuted assertion. | GATE-M0, GATE-M1, GATE-M10, GATE-M11, GATE-M12, GATE-M13, GATE-M14, GATE-M2, GATE-M3, GATE-M4, GATE-M5, GATE-M6, GATE-M7, GATE-M8, GATE-M9, GOV-005, GOV-006 |
| INV-009 | architecture | INV-009-A01 | Child authority, budgets and execution targets are strict subsets of admitted parent authority and resource ceilings. | RUN-004, SEC-001 |
| INV-010 | architecture | INV-010-A01 | A visible product surface is not an authority boundary and cannot introduce independent task, policy, approval, effect or recovery truth. | GOV-007 |
| KNW-001 | knowledge | KNW-001-A01 | Knowledge candidates retain provenance, evidence references, source epoch, confidence, validity interval and conflict information. | KNW-001 |
| KNW-002 | knowledge | KNW-002-A01 | Asynchronous knowledge synthesis rejects stale results when source epoch or relevant task state changed. | KNW-002 |
| KNW-003 | knowledge | KNW-003-A01 | Knowledge Fabric is the single durable semantic knowledge owner; transcript, protocol state and recovery state remain separate. | KNW-003 |
| MAC-001 | machine | MAC-001-A01 | Every execution target has tenant binding, target identity, lifecycle state, execution generation, lease and fence semantics. | MAC-001, MAC-002 |
| MAC-002 | machine | MAC-002-A01 | Worker/guest transport is authenticated, typed, bounded, idempotent and supports ACK/redelivery and cancellation. | MAC-003, MAC-004 |
| MAC-003 | machine | MAC-003-A01 | Hosted isolated task runtimes enforce deny-by-default internal networking and policy-controlled egress. | MAC-004, MAC-005 |
| MAC-004 | machine | MAC-004-A01 | Persistent workspace computers preserve user-authorized workspace state independently of conversational session lifetime. | MAC-006 |
| MAC-005 | machine | MAC-005-A01 | Credentials remain outside guest storage where feasible and guest actions receive only scoped capability handles. | MAC-003 |
| MAC-006 | machine | MAC-006-A01 | Snapshots have explicit workspace-only and full-machine tiers; a checkpoint becomes restorable only after all referenced state is durably committed and verified. | MAC-007 |
| MAC-007 | machine | MAC-007-A01 | Restore and migration advance execution generation so stale pre-restore actions cannot execute. | MAC-007, QA-005 |
| MAC-008 | machine | MAC-008-A01 | Private execution targets use the same command, capability, effect, evidence and recovery semantics as hosted targets. | MAC-008 |
| MOD-001 | model | MOD-001-A01 | The model gateway owns every provider call, credential handle, routing decision, stream and usage settlement. | MOD-001 |
| MOD-002 | model | MOD-002-A01 | Provider adapters translate provider protocols only and cannot own task orchestration, policy, knowledge or business logic. | MOD-002 |
| MOD-003 | model | MOD-003-A01 | Routing selects an allowed model profile from deterministic capability demand, policy, residency, availability and budget constraints without a mandatory prerequisite model call. | MOD-003, MOD-007 |
| MOD-004 | model | MOD-004-A01 | Model streams use the canonical event vocabulary, monotonic sequence, explicit terminal state, backpressure and cancellation. | MOD-004, MOD-007 |
| MOD-005 | model | MOD-005-A01 | Usage reservations and provider usage settle idempotently, including usage arriving after cancellation, without rewriting historical settlement. | MOD-005, QA-002, RUN-007 |
| MOD-006 | model | MOD-006-A01 | Privacy/residency enforcement occurs before provider egress and denial results in zero protected bytes crossing the blocked boundary. | MOD-006, QA-002, SEC-003 |
| MOD-007 | model | MOD-007-A01 | Every enabled provider profile passes real request, stream, cancellation, usage, malformed-response and outage qualification. | MOD-008, QA-002 |
| REL-001 | release | REL-001-A01 | A release candidate binds exact source commit, generated bindings, service/client artifacts, images, configuration, migrations and support selection. | REL-001, REL-006 |
| REL-002 | release | REL-002-A01 | Any rebuild or source/configuration change after candidate creation creates a new candidate and invalidates candidate-specific qualification. | REL-001 |
| REL-003 | release | REL-003-A01 | Candidate qualification requires every mapped blocking suite to pass for the exact candidate and enabled support profiles. | REL-002, REL-005, REL-006 |
| REL-004 | release | REL-004-A01 | Canary deployment and rollback operate on the exact qualified candidate and preserve data/effect compatibility. | REL-003, REL-004, REL-008 |
| REL-005 | release | REL-005-A01 | Only GATE-M14 may transition an eligible candidate to PRODUCTION_READY. | GATE-M14, REL-007 |
| REL-006 | release | REL-006-A01 | Production promotion is a separate authorized operation of the exact PRODUCTION_READY candidate and records post-deploy verification. | REL-008 |
| RUN-001 | runtime | RUN-001-A01 | WorkGraph, AgentGraph and StateGraph have canonical persisted identities and are mutated only through GraphTransaction. | RUN-001, RUN-003 |
| RUN-002 | runtime | RUN-002-A01 | Persistent teammates and ephemeral workers have explicit lifecycle, ownership, workspace binding and capability snapshots. | COL-004, RUN-002 |
| RUN-003 | runtime | RUN-003-A01 | Worker admission atomically reserves capacity, budget and capability before the child becomes externally visible. | RUN-004 |
| RUN-004 | runtime | RUN-004-A01 | Asynchronous fan-out/fan-in produces independently durable incremental child outcomes and supports partial completion. | COL-001, COL-002, QA-001, RUN-005 |
| RUN-005 | runtime | RUN-005-A01 | Parent cancellation stops undispatched work, requests cancellation of cancellable work, preserves committed effects and returns partial outcomes. | RUN-006 |
| RUN-006 | runtime | RUN-006-A01 | Budget reservations are atomic under concurrency and cannot oversubscribe the parent budget, including retries, restarts and late settlements. | MOD-005, RUN-007, SRE-006 |
| RUN-007 | runtime | RUN-007-A01 | Durable waits and callbacks survive runtime restart without holding a process or duplicating resumed work. | RUN-008 |
| RUN-008 | runtime | RUN-008-A01 | Task, agent, workspace, approval and execution lifetime are independent of interactive client process lifetime. | COL-003, DAT-003, MAC-006, QA-001, RUN-005, UX-007 |
| SEC-001 | security | SEC-001-A01 | CapabilitySnapshot is immutable for an admitted step and child capabilities are strict subsets of the parent snapshot. | AUT-003, RUN-004, SEC-001, SKL-005 |
| SEC-002 | security | SEC-002-A01 | Policy decisions bind actor, operation, normalized arguments, target, data class, capability snapshot and decision version. | SEC-002 |
| SEC-003 | security | SEC-003-A01 | Sensitive data is classified before remote egress and policy can allow, redact, require approval or deny by destination and data class. | MOD-006, SEC-003 |
| SEC-004 | security | SEC-004-A01 | Credential access uses short-lived scoped handles and never exposes reusable plaintext secrets to untrusted clients or guests. | EXT-002, SEC-004 |
| SEC-005 | security | SEC-005-A01 | Behavior-sequence rules can block or escalate dangerous multi-step combinations of otherwise individually permitted operations. | SEC-005 |
| SEC-006 | security | SEC-006-A01 | Tenant isolation is enforced at command, storage, event, artifact, model, connector, worker and machine boundaries. | DAT-001, DAT-008, MAC-005, SEC-006 |
| SEC-007 | security | SEC-007-A01 | Execution generation, exclusive lease and fence token prevent stale endpoint or guest actions from executing. | BRW-006, MAC-001, MAC-002 |
| SEC-008 | security | SEC-008-A01 | Supply-chain qualification binds the exact source commit, dependency lockfiles, generated bindings, images and release artifacts. | REL-001, SEC-007 |
| SKL-001 | skills | SKL-001-A01 | Controlled Skill Evolution converts authoritative material into candidate SkillPackages through decomposition and procedural reconstruction. | SKL-001 |
| SKL-002 | skills | SKL-002-A01 | Candidate skills pass static, security, sandbox and regression evaluation before governed promotion. | QA-006, SKL-002, SKL-003 |
| SKL-003 | skills | SKL-003-A01 | A skill cannot self-promote, expand its own authority, bypass evaluation or introduce another execution runtime. | SKL-002, SKL-004 |
| SKL-004 | skills | SKL-004-A01 | Skill registry versions, compatibility, evaluation thresholds, rollback target and promotion state are explicit and durable. | SKL-004 |
| SKL-005 | skills | SKL-005-A01 | Runtime materializes only task-required qualified skills through Capability Projection and removes task-scoped materialization after use. | SKL-005 |
| SRE-001 | sre | SRE-001-A01 | Core authenticated command/event API targets 99.95% monthly availability and exposes SLI/SLO telemetry tied to canonical request/run identities. | SRE-001, SRE-002 |
| SRE-002 | sre | SRE-002-A01 | Authoritative state targets RPO <=300 seconds and RTO <=1800 seconds; evidence/object state targets RPO <=900 seconds and RTO <=3600 seconds. | QA-008, SRE-004 |
| SRE-003 | sre | SRE-003-A01 | RecoveryConsistencyPoint binds database commit position, RuntimeEvent sequence, evidence manifest, snapshot inventory, effect-settlement watermark and unresolved UNKNOWN effects. | MAC-007, QA-008, SRE-003, SRE-004 |
| SRE-004 | sre | SRE-004-A01 | Command admission p95 <=500 ms excluding external provider/tool latency; event projection lag p95 <=2 seconds under qualified load. | SRE-002, SRE-005 |
| SRE-005 | sre | SRE-005-A01 | Warm isolated task runtime readiness p95 <=20 seconds and cold readiness p95 <=60 seconds for the qualified hosted configuration. | SRE-002, SRE-005 |
| SRE-006 | sre | SRE-006-A01 | Load, soak, quota, cost, degradation and disaster-recovery tests run against production-like topology before candidate qualification. | SRE-005, SRE-006 |
| UX-001 | frontend | UX-001-A01 | Desktop workbench provides persistent teammate, task, research, capability, automation, approval, evidence and live workspace surfaces over canonical APIs. | UX-001, UX-005 |
| UX-002 | frontend | UX-002-A01 | Every client rebuilds from snapshot plus ordered RuntimeEvent cursor and tolerates duplicate/out-of-order delivery without becoming authority. | QA-007, UX-002 |
| UX-003 | frontend | UX-003-A01 | Approval UI displays exact semantic effect scope and cannot approve a hidden or changed operation. | UX-004 |
| UX-004 | frontend | UX-004-A01 | Live browser/computer UI exposes observation, takeover state, controller identity and return-of-control without restarting the session. | UX-003 |
| UX-005 | frontend | UX-005-A01 | Web, mobile and CLI clients use the same canonical commands/events and may not introduce local shadow execution. | UX-006, UX-007, UX-008 |
| UX-006 | frontend | UX-006-A01 | Supported client surfaces meet keyboard, focus, assistive-label, reduced-motion and non-color-only status requirements. | UX-001 |


---

<!-- source: docs/35_ARCHITECTURE_DECISION_TEMPLATE.md -->

# 35 — Architecture decision template

```text
Decision ID:
Owner:
Status: PROPOSED | ACCEPTED | REJECTED | RETIRED
Context:
Problem:
Decision:
Alternatives considered:
Affected architectural invariants:
Affected canonical owners/schemas/wiring:
Threat/privacy/tenant impact:
Data migration/compatibility impact:
Rollback/reversal plan:
Testing/qualification impact:
Review trigger/date:
```

Decision records do not mark implementation tasks complete. A decision that changes canonical registry truth must update the registry/source and regenerate all reading views.


---

<!-- source: docs/36_FRONTEND_STATE_AND_INTERACTION_CONTRACT.md -->

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


---

<!-- source: docs/37_IMPLEMENTATION_EVIDENCE_FORMAT.md -->

# 37 — Implementation evidence format

Completion is reproducibility-based, not signature-based.

`VerificationReport` contains task, repository/commit/protected ref, CI run/pipeline identity, environment/configuration digest, PASS/FAIL/BLOCKED state, assertion results, artifact identities/digests/verification method, real-boundary state and execution time.

`ImplementationEvidence` contains exact requirement IDs, task assertion IDs and requirement assertion IDs; repository commit; report path/digest; artifact digests; real-boundary and rollback state.

Validator rules:
1. task exists;
2. requirement IDs exactly equal task requirement IDs;
3. task assertion IDs exactly equal blocking task assertions;
4. requirement assertion IDs exactly equal linked requirement assertion IDs;
5. commit exists and is reachable from configured qualification ref;
6. report exists and digest matches;
7. report belongs to the same task/commit/environment;
8. every blocking assertion PASS for completion;
9. local artifacts hash to declared digests; remote artifacts require digest lookup or trusted build attestation receipt;
10. `real_boundary=true` when task requires it;
11. `BLOCKED_REAL_BOUNDARY` never closes work.


---

<!-- source: docs/38_IMPLEMENTATION_KICKOFF.md -->

# 38 — Implementation kickoff

Read `AGENTS.md`, `HANDOFF.md`, master dossier, implementation plan, task/requirement registries, schemas, wiring, support/qualification/release registries, repository implementation map and completion/evidence contracts.

Begin at the earliest DAG-ready task whose dependencies have valid evidence. Do not repeat a completed repository task unless its governed inputs changed or its evidence no longer validates.

Continuous loop:
`READ → TASK-SPECIFIC RECONCILIATION → PLAN → IMPLEMENT → MIGRATE → TEST → ADVERSARIAL TEST → RECOVERY TEST → VERIFY → EVIDENCE → NEXT`

Stop only for a genuine authority contradiction, unavailable required real boundary, operation requiring human authorization, or unsafe/destructive migration without an approved rollback. Otherwise continue to the next ready task.


---

<!-- source: docs/39_REPOSITORY_EXECUTION_SEQUENCE.md -->

# 39 — Repository execution sequence

Implementation begins from the current repository bytes, not from assumptions. The first governance slice establishes exact repository ownership/disposition, canonical schema/binding gates, reproducible evidence, source completeness and qualification environment. From then on, every task performs only task-specific reconciliation.

The application currently contains useful Python/FastAPI/tool/provider/context code that may be migrated behind canonical owners, alongside conflicting process-local and parallel execution paths that cannot remain production authority. Use `docs/31_CURRENT_REPOSITORY_IMPLEMENTATION_MAP.md`; do not discard reusable adapter/domain logic solely because its current owner is wrong.

The intended sequence is the machine-readable DAG. Milestone gates cannot be manually bypassed. Foundational capability admission is implemented in the data/foundation milestone before worker/model/tool admission depends on it. Protected effect policy is in place before browser/connector consequential actuation. Production promotion occurs only after the readiness gate.


---

<!-- source: docs/40_CONTRACT_CONFORMANCE_FIXTURES.md -->

# 40 — Contract conformance fixtures

Every canonical schema has a positive fixture under `tests/fixtures/valid/` and a corresponding negative fixture under `tests/fixtures/invalid/`. Positive fixtures must validate and negative fixtures must fail. Coverage equality between the schema registry and both fixture directories is itself release-blocking. The fixture set explicitly includes:

- model request identity/generation/routing/budget/context fields;
- canonical `ModelEvent.event_type` vocabulary;
- endpoint generation, lease, fence, capability, policy, effect and approval scope;
- typed non-executable SearchProgram predicates;
- reproducible implementation evidence and blocking assertion results;
- immutable graph and capability identities;
- support/qualification selection and release ownership.

A validator that accepts a deliberately invalid fixture fails qualification even if all valid fixtures pass.


---

<!-- source: docs/41_SECURITY_DEPENDENCY_ORDER.md -->

# 41 — Security dependency order

Security is introduced at the first dependent boundary rather than deferred to a final hardening phase.

1. Authenticated tenant/session authority precedes authoritative commands.
2. Foundational immutable CapabilitySnapshot precedes agent/worker/model/tool/machine admission.
3. Model privacy/residency enforcement precedes real provider qualification.
4. Argument-bound policy, destination-aware privacy, credential brokerage and behavior-sequence guards precede consequential effects.
5. Effect Ledger and scoped approval precede connector/browser consequential actuation.
6. Lease/generation/fence enforcement precedes guest or endpoint actuation.
7. Tenant-isolation adversarial tests and build/artifact provenance are repeated at production qualification.

Later security milestones may strengthen controls but cannot be the first implementation of a prerequisite used by an earlier feature.


---

<!-- source: docs/42_RELEASE_STATE_OWNERSHIP.md -->

# 42 — Release state ownership

`GATE-M14` is the only owner allowed to write `PRODUCTION_READY`. Release tasks before the gate create, qualify, canary, rollback-test, decide and seal readiness evidence for an immutable candidate. The separate production-promotion task depends on `GATE-M14` and therefore cannot be used as evidence required to reach production readiness.

Any source, artifact, configuration, migration or support-selection change after candidate creation creates a new candidate identity and invalidates candidate-bound qualification reuse.


---

<!-- source: docs/43_FRONTEND_COMPONENT_ARCHITECTURE.md -->

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


---

<!-- source: docs/44_BACKEND_SERVICE_INTERNALS.md -->

# 44 — Backend service internals and package layout

The canonical service names define ownership, not a requirement that every owner starts as an independently deployed process. Early deployment may co-locate owners, but packages, persistence boundaries and interfaces must preserve the final ownership model so extraction does not require rewriting authority.

## Recommended repository layout

```text
cmd/
  quansio-api/
  quansio-control/
  quansio-runtime/
  quansio-model-gateway/
  quansio-context/
  quansio-indexer/
  quansio-worker-gateway/
  quansio-machine-control/
  quansio-integration-broker/
  quansio-artifact/
  quansio-notify/
  qworkerd/
internal/
  auth/
  control/
  runtime/
  modelgateway/
  context/
  indexer/
  workers/
  machines/
  integrations/
  artifacts/
  notifications/
  policy/
  effects/
  observability/
generated/
  contracts/
migrations/
clients/
deploy/
tests/
```

Equivalent language-specific organization is acceptable if canonical imports and owner rules remain mechanically enforceable.

## Request admission

`quansio-api` authenticates transport identity, resolves tenant/workspace/session from server state, validates canonical command revision/idempotency, applies coarse request limits and forwards the command to its owner. It does not call model providers, connectors or guest actuators.

`quansio-control` owns mutable administrative truth and emits versioned snapshots/decisions. Runtime steps bind exact IDs/revisions at admission rather than re-reading mutable configuration midway through an effect.

## Runtime transaction boundary

A runtime transition loads expected graph/agent/state revisions, validates preconditions, applies GraphTransaction, persists protocol changes, appends RuntimeEvent/outbox and commits atomically. External providers are never called while a database transaction is held. External effects use the Effect Ledger state machine around actuation.

## Concurrency

Use optimistic revision checks or row-level locks only at the canonical aggregate boundary. Worker admission and budget reservation must be atomic. Run/step transitions are idempotent by transaction/command identity. Duplicate network delivery never means duplicate state mutation.

## Internal APIs

Internal APIs use generated canonical contracts plus service-specific typed requests where the request is not a durable/wire authority object. Do not share mutable in-memory runtime objects across owners as a hidden internal API. Timeouts, cancellation, trace IDs and tenant identity propagate across calls.

## Error handling

Expected failures are typed domain outcomes. Unexpected errors are observable failures, not success fallbacks. Services must not catch broad exceptions and synthesize empty/default success. Retries are bounded, jittered where appropriate and only used for operations whose idempotency/reconciliation contract permits them.

## Deployment health

Each deployable exposes liveness separately from readiness. Readiness checks owner-critical dependencies and migrations/configuration. A process can remain live while being unready. Readiness failure must not route new work into a service that cannot safely satisfy its owner contract.


---

<!-- source: docs/45_DATA_AND_EVENT_TOPOLOGY.md -->

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


---

<!-- source: docs/46_MODEL_GATEWAY_IMPLEMENTATION.md -->

# 46 — Model gateway implementation contract

## Admission pipeline

```text
Runtime step
  → ContextProjection
  → CapabilityDemand
  → capability/policy/residency/budget validation
  → deterministic route decision
  → usage reservation
  → ModelRequestEnvelope
  → provider adapter
  → canonical ModelEvent stream
  → usage settlement
```

No client/worker/skill/connector can invoke a provider outside this path.

## Provider adapter interface

A provider adapter implements only protocol translation:

```text
validate_profile(profile)
start(request_envelope) -> provider_stream_handle
translate_event(provider_event) -> ModelEvent | internal-noop
cancel(cancellation_id)
query/settle_usage(request_id) -> usage record
classify_provider_error(error) -> retryability/failure class
```

It receives a normalized request, not unrestricted task state. Credentials are resolved inside the gateway through server-side secret handles.

## Routing

Routing input is a versioned CapabilityDemand plus allowed model catalog, policy, residency, provider health and budget. The decision produces `route_decision_id`, selected `model_profile_id`, catalog revision and reason codes. A provider/model is never selected if it violates an admission constraint even if it scores better on capability.

## Streaming state

Canonical model events use monotonic sequence and exactly one terminal state. Provider-specific aliases are translated in the adapter. Duplicate provider deltas are deduplicated when the provider offers identity; otherwise gateway sequencing and persisted stream state prevent duplicate downstream application.

## Cancellation and usage

Cancellation marks the request cancellation state and attempts provider cancellation. The usage reservation is not released as zero immediately: it enters settlement until the provider's final/late usage is known or the profile-specific settlement deadline expires. Late charges/credits are append-only adjustments.

## Failover

Automatic failover is allowed only before a consequential downstream interpretation depends on ambiguous partial model output, or when the task contract explicitly permits restarting with a new request identity. A provider error cannot cause two model outputs to be presented as one continuous request without explicit lineage.

## Privacy

Before provider egress, content classification and destination/residency policy decide allow/redact/deny. The denied-path qualification captures outbound bytes at the gateway boundary and proves protected content was not transmitted.


---

<!-- source: docs/47_QWORKERD_GUEST_PROTOCOL.md -->

# 47 — qworkerd guest protocol and execution boundary

`qworkerd` is a constrained actuator, not an agent brain. It does not own task truth, policy, credentials, model routing or durable business state.

## Session establishment

The worker gateway presents a target-bound session token/transport identity. `qworkerd` validates target identity, execution generation and lease/fence context before accepting operations. Session renewal cannot lower the fence or resurrect an expired generation.

## Operation envelope

Guest operations carry:

```text
operation_id / version
request_id / delivery_id / idempotency_key
tenant + target
execution_generation
lease_id + fence_token
capability_snapshot_id
policy/effect references where consequential
timeout/cancellation identity
arguments
```

The guest rejects stale generation/fence before invoking filesystem/process/browser actuators.

## Filesystem

Mounts are explicit and task/workspace scoped. Protected paths are denied unless the admitted capability permits them. Artifact inputs are digest-verified before use. Outputs become artifacts through the artifact service rather than escaping as untracked guest paths.

## Process/terminal

Commands use typed executable, argv, cwd, environment overlay, stdin mode, timeout, output limits and streaming identity. Shell string execution is not the default contract. Secret handles are materialized only for the exact operation when unavoidable and are scrubbed from logs/output.

## Network

Egress is deny-by-default and policy-controlled. DNS, TCP/HTTP proxy and browser traffic are attributable to target/run/operation. Internal control-plane addresses are not reachable unless explicitly part of the guest protocol.

## Delivery

A completed operation is stored under idempotency/delivery identity before ACK. Lost ACK causes result redelivery, not re-execution. Ambiguous host-side consequential effects follow the Effect Ledger reconciliation contract.


---

<!-- source: docs/48_BUSINESS_CAPABILITY_COMPILER_IMPLEMENTATION.md -->

# 48 — Business Capability Compiler implementation

The Capability Compiler is an authoring pipeline that produces qualified Business Capability Packs. It is not a runtime scheduler.

## Inputs

- authoritative documents and knowledge records;
- SOPs/process maps;
- API/OpenAPI/connector schemas;
- policy and RBAC definitions;
- approval matrices;
- examples and historical successful work with evidence;
- existing qualified skills/tools;
- version/compatibility constraints.

Every input carries source identity, version/digest, tenant/owner scope and classification.

## Compiler stages

1. **Ingest and normalize** — resolve source identity, structure, permissions and freshness.
2. **Semantic decomposition** — identify actors, objects, decisions, preconditions, outputs and exception paths.
3. **Process reconstruction** — create candidate workflow graph including waits, approvals, compensations and evidence points.
4. **Skill resolution** — bind existing qualified skills; generate candidates only when no qualified skill matches.
5. **Tool/connector binding** — resolve versioned operations and fidelity classes.
6. **RBAC/policy binding** — map roles, permission atoms, data classes, target restrictions and approval rules.
7. **I/O/evidence contract generation** — define typed inputs, outputs and proof required for completion.
8. **Evaluation generation** — positive, adversarial, recovery and compatibility cases.
9. **Qualification** — execute pack tests using normal WorkGraph/runtime infrastructure.
10. **Publish** — store immutable pack version and dependencies in registry.

## Runtime resolution

Installing a pack never copies ambient credentials or authority. At work admission, control/runtime resolve pack version, compatible skill/tool versions and current user's allowed CapabilitySnapshot. Missing permissions or incompatible connector versions produce a typed admission failure.

## Updates

A source/API/policy change creates a candidate new pack version and impact analysis. It never mutates a published version in place. Historical runs retain the exact pack/skill/tool versions they used.


---

<!-- source: docs/49_CONTROLLED_SKILL_EVOLUTION_IMPLEMENTATION.md -->

# 49 — Controlled Skill Evolution implementation

## Skill candidate construction

A candidate SkillPackage is produced from authoritative source refs plus a procedural reconstruction. It declares purpose, intended use, exclusions, I/O contracts, instructions, dependencies, capability requirements, compatibility and evaluation thresholds.

## Static gate

Reject candidates containing undeclared executable dependencies, direct provider/credential access, alternate orchestration loops, forbidden host paths, authority-expansion instructions or unresolved placeholders. Instruction content is data to the runtime; it cannot override policy or canonical tool contracts.

## Evaluation

Evaluation uses an isolated task runtime and representative fixtures/real boundaries according to the skill. It measures correctness, side effects, evidence, latency/cost and failure behavior. Security cases attempt prompt/tool injection, scope expansion, protected-data exfiltration and tool-operation substitution.

## Promotion

Promotion is a control-plane registry transition performed only when all required evaluations meet thresholds. Runtime success alone never promotes a candidate. Promotion records exact package digest, evaluation result IDs and compatibility window.

## Materialization

Capability Projection selects only task-relevant qualified skills. Machine materialization places versioned content in the target or projects it into model context according to the skill type. Materialization never copies registry write authority into the target.

## Rollback/deprecation

Rollback changes future resolution to a qualified rollback target while historical work remains pinned. Deprecated versions can remain readable for evidence/replay but are not selected for new work after policy cutoff.


---

<!-- source: docs/50_CI_AND_REAL_ENVIRONMENT_BLUEPRINT.md -->

# 50 — CI and real-environment blueprint

## Pipeline stages

```text
authority-check
  → generated-contract/build check
  → unit/static/security scan
  → migration/contract tests
  → durable integration environment
  → runtime/effect integration
  → real provider/browser/machine/connector suites as mapped
  → E2E vertical slices
  → load/DR/security qualification
  → immutable candidate build
  → candidate-bound qualification
  → canary/rollback
```

Blocking stages cannot be converted to warnings or `|| true`. A flaky test remains a failure until root-caused; retries may collect diagnostics but cannot turn an unexplained first failure into release PASS.

## Integration environment

Provision isolated identities for PostgreSQL, durable event transport, Redis/lease store and object storage. Seed only through migrations/fixtures. Health and teardown are recorded. Integration runs may not substitute in-memory stores for durability requirements.

## External qualification

Provider, browser, machine and connector suites use test/sandbox accounts or isolated real accounts where available. Secrets are injected by CI/environment secret management and never committed. If a required boundary is unavailable, produce `BLOCKED_REAL_BOUNDARY`, not a fake success.

## Candidate build

Build once from a reachable commit. Record source commit, dependency lock digests, container/binary digests, migration-set digest, configuration digest and support-selection digest. Candidate qualification, canary and production promotion all refer to those exact identities.

## Test reports

Each report lists exact assertion IDs and artifact identities. Completion evidence references the report by digest. The evidence validator independently checks repository reachability, report result, assertion coverage and artifact identity.


---

<!-- source: docs/51_THREAT_MODEL_AND_ABUSE_CASES.md -->

# 51 — Threat model and abuse cases

The implementation threat model must cover at least:

- forged tenant/user/workspace identity from clients or webhooks;
- stale/expanded CapabilitySnapshot;
- policy/approval TOCTOU and argument mutation after approval;
- low-level browser actions hiding a consequential semantic effect;
- credential leakage into model context, guest environment, logs or artifacts;
- prompt/tool injection attempting authority expansion;
- worker/endpoint replay after lease/generation/fence changes;
- duplicate delivery causing duplicate payment/message/delete;
- ambiguous external timeout followed by unsafe retry;
- cross-tenant object IDs, cache keys, event subjects, search indexes and artifacts;
- malicious skill/capability package dependency or self-promotion attempt;
- provider/connector webhook spoofing and duplicate delivery;
- sandbox escape, protected-path read/write and internal-network reachability;
- browser takeover race between agent and human controller;
- model/data residency violation;
- stale knowledge synthesis after fork/revert/source change;
- poisoned research source/evidence mismatch;
- compromised build artifact or candidate substitution;
- operator/admin misuse of RBAC/policy/support settings;
- backup restore that replays committed effects.

Every threat maps to preventive controls, detection telemetry, negative tests and recovery/incident handling. Security-critical control failures fail closed.


---

<!-- source: docs/52_OPERATIONAL_RUNBOOKS.md -->

# 52 — Operational runbooks required before production

Create and qualify runbooks for:

1. API/control/runtime partial outage and safe traffic drain.
2. Database failover and RecoveryConsistencyPoint validation.
3. Durable event transport outage/backlog and outbox catch-up.
4. Model provider outage, route disablement and usage reconciliation.
5. Connector outage/webhook backlog and consequential-effect UNKNOWN handling.
6. Worker pool exhaustion and admission backpressure.
7. Machine target unhealthy/migration/restore and generation advance.
8. Browser fleet degradation and human-session preservation.
9. Credential compromise/revocation without exposing secret material.
10. Cross-tenant incident containment and evidence preservation.
11. Artifact/object-store restore and digest verification.
12. Skill or Business Capability emergency disable/rollback.
13. Automation scheduler outage and missed-fire policy handling.
14. Candidate canary rollback and production rollback.
15. Support-profile disablement when qualification no longer holds.

Each runbook names owner/on-call, trigger signals, containment steps, commands/tools, data/effect safety checks, rollback/recovery, communication and post-incident evidence. Runbooks are exercised during qualification; existence of Markdown alone is not acceptance.


---

<!-- source: docs/CODE_QUALITY_IMPROVEMENT_PLAN.md -->

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
