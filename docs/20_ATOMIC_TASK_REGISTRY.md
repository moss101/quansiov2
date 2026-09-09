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
