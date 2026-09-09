# 38 — Implementation kickoff

Read `AGENTS.md`, `HANDOFF.md`, master dossier, implementation plan, task/requirement registries, schemas, wiring, support/qualification/release registries, repository implementation map and completion/evidence contracts.

Begin at the earliest DAG-ready task whose dependencies have valid evidence. Do not repeat a completed repository task unless its governed inputs changed or its evidence no longer validates.

Continuous loop:
`READ → TASK-SPECIFIC RECONCILIATION → PLAN → IMPLEMENT → MIGRATE → TEST → ADVERSARIAL TEST → RECOVERY TEST → VERIFY → EVIDENCE → NEXT`

Stop only for a genuine authority contradiction, unavailable required real boundary, operation requiring human authorization, or unsafe/destructive migration without an approved rollback. Otherwise continue to the next ready task.
