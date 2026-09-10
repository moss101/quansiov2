# Support mappings

Generated from registries/support-matrix.json by tools/governance/generate_authority.py 1.0.0. DO NOT EDIT.

| Profile | Kind | Status | Required suites | Qualification tasks | Enabled when |
|---|---|---|---|---|---|
| browser.managed.primary | browser | REQUIRED_GA | Q-BROWSER, Q-EFFECT, Q-SECURITY | BRW-008, QA-004, QA-005 | ALL_REQUIRED_SUITES_PASS |
| client.cli.primary | client | REQUIRED_GA | Q-AUTH, Q-CLIENT | QA-007, UX-008 | ALL_REQUIRED_SUITES_PASS |
| client.desktop.primary | client | REQUIRED_GA | Q-AUTH, Q-CLIENT, Q-SECURITY | QA-007, UX-001, UX-002, UX-003, UX-004 | ALL_REQUIRED_SUITES_PASS |
| client.mobile.primary | client | DISABLED_UNTIL_QUALIFIED | Q-AUTH, Q-CLIENT, Q-SECURITY | QA-007, UX-007 | ALL_REQUIRED_SUITES_PASS |
| client.web.primary | client | REQUIRED_GA | Q-AUTH, Q-CLIENT, Q-SECURITY | QA-007, UX-006 | ALL_REQUIRED_SUITES_PASS |
| execution.hosted_microvm.primary | execution | REQUIRED_GA | Q-DR, Q-MACHINE, Q-SECURITY | MAC-005, MAC-007, QA-005, QA-008 | ALL_REQUIRED_SUITES_PASS |
| execution.local_virtualized.primary | execution | DISABLED_UNTIL_QUALIFIED | Q-MACHINE, Q-SECURITY | MAC-008, QA-005 | ALL_REQUIRED_SUITES_PASS |
| execution.persistent_workspace.primary | execution | REQUIRED_GA | Q-BROWSER, Q-DR, Q-MACHINE | MAC-006, MAC-007, QA-005 | ALL_REQUIRED_SUITES_PASS |
| execution.private_worker.primary | execution | DISABLED_UNTIL_QUALIFIED | Q-MACHINE, Q-SECURITY | MAC-008, QA-005 | ALL_REQUIRED_SUITES_PASS |
| model.primary_profile | model | REQUIRED_GA | Q-MODEL, Q-SECURITY | MOD-008, QA-002 | ALL_REQUIRED_SUITES_PASS |
| model.secondary_profile | model | DISABLED_UNTIL_QUALIFIED | Q-MODEL, Q-SECURITY | MOD-008, QA-002 | ALL_REQUIRED_SUITES_PASS |

## Qualification suites

- `Q-AUTH` — Authority, identity and tenant isolation tasks: DAT-001, DAT-008, GOV-002, GOV-003, SEC-006
- `Q-AUTOMATION` — Automation and collaboration tasks: AUT-001, AUT-002, AUT-003, AUT-004, COL-001, COL-002, COL-003, COL-004, QA-007
- `Q-BROWSER` — Browser and endpoint control tasks: BRW-001, BRW-002, BRW-003, BRW-004, BRW-005, BRW-006, BRW-007, BRW-008, QA-005
- `Q-BUSINESS` — Business Capability Packs and compiler tasks: BUS-001, BUS-002, BUS-003, BUS-004, BUS-005, EXT-001, EXT-002, EXT-003, QA-006
- `Q-CANARY` — Candidate, canary and rollback tasks: GATE-M14, REL-001, REL-002, REL-003, REL-004, REL-005, REL-006, REL-007
- `Q-CLIENT` — Desktop, web, mobile and CLI tasks: QA-007, UX-001, UX-002, UX-003, UX-004, UX-005, UX-006, UX-007, UX-008
- `Q-DATA` — Durable data, event and protocol state tasks: DAT-002, DAT-003, DAT-004, DAT-005, DAT-006, QA-008
- `Q-DR` — Backup, restore and recovery consistency tasks: QA-008, SRE-003, SRE-004
- `Q-EFFECT` — Policy, approvals and effects tasks: EFF-001, EFF-002, EFF-003, QA-004, SEC-001, SEC-002, SEC-003, SEC-004, SEC-005
- `Q-LOAD` — Load, soak, quota and cost tasks: SRE-002, SRE-005, SRE-006
- `Q-MACHINE` — Worker and machine fabric tasks: MAC-001, MAC-002, MAC-003, MAC-004, MAC-005, MAC-006, MAC-007, MAC-008, QA-005
- `Q-MODEL` — Server model fulfillment tasks: MOD-001, MOD-002, MOD-003, MOD-004, MOD-005, MOD-006, MOD-007, MOD-008, QA-002
- `Q-RESEARCH` — Evidence-first research tasks: CTX-001, CTX-002, CTX-003, CTX-004, CTX-005, CTX-006, CTX-007, CTX-008, QA-003
- `Q-RUNTIME` — Graph runtime, workers, budgets and recovery tasks: QA-001, RUN-001, RUN-002, RUN-003, RUN-004, RUN-005, RUN-006, RUN-007, RUN-008
- `Q-SECURITY` — Security and isolation tasks: BRW-003, MAC-002, QA-004, QA-005, SEC-001, SEC-002, SEC-003, SEC-004, SEC-005, SEC-006
- `Q-SKILL` — Knowledge and controlled skill evolution tasks: KNW-001, KNW-002, KNW-003, QA-006, SKL-001, SKL-002, SKL-003, SKL-004, SKL-005
