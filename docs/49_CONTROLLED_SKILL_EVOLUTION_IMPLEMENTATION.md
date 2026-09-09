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
