# Implementation handoff

Use this package as the sole active implementation authority. Implementation begins at the earliest DAG-ready task whose dependencies have valid evidence. Do not restart completed work merely to gain familiarity; re-open a task only when its governed inputs materially changed or its evidence fails current validation.

The target is a production platform, not a prototype. Every feature must be wired end-to-end through canonical owners, real durable boundaries and the defined qualification suites.

The master dossier is a reading view. Machine-readable truth for tasks, requirements, dependencies, schemas, support and release state lives under `registries/` and `schemas/`. Generated reading views must match those sources exactly.
