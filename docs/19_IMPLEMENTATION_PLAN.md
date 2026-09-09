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
