# 35 — Architecture decision record

```text
Decision ID: ADR-0003
Owner: architecture
Status: ACCEPTED
Context: GOV-007 requires an enforceable workflow for architecture decisions
and threat-model changes. The authority template (doc 35) prescribes the
record fields. Without a mechanical gate, a canonical owner or effect/security
invariant could be changed in the registry without a decision record.
Problem: Enforce that every canonical-owner, effect-path or security-invariant
change cites an accepted decision record, and that decision records stay
consistent with canonical registry truth (no orphaned task/schema references,
no retired decisions still governing owners).
Decision: All decision records live in `docs/decisions/` in the doc-35
template format with machine-parseable fields.
`tools/governance/decision_gate.py` enforces: every record carries all
template fields; Status is one of PROPOSED|ACCEPTED|REJECTED|RETIRED;
referenced task IDs exist in `registries/tasks.json`; referenced schema files
exist; records governing canonical services (via
`evidence/ownership/ownership_registry.json` decision_id references) are
ACCEPTED. Changing a canonical owner, effect class or security invariant
without a new accepted decision record fails the gate, which runs in
`verify_all` (CI blocks the change). Rollback of a decision means marking it
RETIRED and restoring the prior registry state in the same change; the gate
fails while any registry entry still cites a RETIRED/REJECTED/PROPOSED
decision.
Alternatives considered: Git-history-only enforcement (not mechanical for
registry-content changes); trusting review process alone (explicitly
rejected by GOV-007-N01); embedding decision text inside the registry
(duplicates authority and risks drift).
Affected architectural invariants: INV-004 (one effect path), INV-010
(clients are not authority) are protected by requiring decisions for any
effect/security change; INV-006 composition unchanged.
Affected canonical owners/schemas/wiring: adds `decision_id` to canonical
service entries in the ownership registry; no schema changes.
Threat/privacy/tenant impact: Threat-model and abuse-case changes now route
through the same record+gate workflow, so security-relevant architecture
changes cannot bypass review.
Data migration/compatibility impact: none.
Rollback/reversal plan: Mark the decision RETIRED, restore the prior
registry entries and regenerate derived views; the gate verifies no orphaned
references remain.
Testing/qualification impact: GOV-007 acceptance suite exercises the gate
positively, negatively and through a full decision rollback cycle.
Review trigger/date: Any template change in doc 35 or new registry field
governed by decisions; review 2026-12-10.
```
