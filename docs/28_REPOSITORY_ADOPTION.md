# 28 — Repository adoption and implementation placement

Before implementing a task, inspect the current repository and classify relevant code as `ALREADY_COVERED`, `PARTIAL`, `GENUINE_GAP`, `CONFLICT`, `IMPLEMENTED_UNDOCUMENTED`; then choose disposition `REUSE_BEHIND_OWNER`, `MIGRATE`, `FREEZE_THEN_REMOVE`, `REMOVE_NOW`, or `BUILD`.

Reusable protocol translation/domain code may survive only behind the correct canonical owner. A reusable helper does not inherit architectural authority from its current location.

Do not create a new database, queue, browser stack, orchestrator, memory system or model/provider path because a task lacks an obvious home. Use the service ownership table and wiring first; if the requirement truly cannot fit a canonical owner, open an architecture decision rather than implementing a convenience subsystem.
