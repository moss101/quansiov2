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
