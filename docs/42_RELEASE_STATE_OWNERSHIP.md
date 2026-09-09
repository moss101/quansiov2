# 42 — Release state ownership

`GATE-M14` is the only owner allowed to write `PRODUCTION_READY`. Release tasks before the gate create, qualify, canary, rollback-test, decide and seal readiness evidence for an immutable candidate. The separate production-promotion task depends on `GATE-M14` and therefore cannot be used as evidence required to reach production readiness.

Any source, artifact, configuration, migration or support-selection change after candidate creation creates a new candidate identity and invalidates candidate-bound qualification reuse.
