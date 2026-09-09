# 48 — Business Capability Compiler implementation

The Capability Compiler is an authoring pipeline that produces qualified Business Capability Packs. It is not a runtime scheduler.

## Inputs

- authoritative documents and knowledge records;
- SOPs/process maps;
- API/OpenAPI/connector schemas;
- policy and RBAC definitions;
- approval matrices;
- examples and historical successful work with evidence;
- existing qualified skills/tools;
- version/compatibility constraints.

Every input carries source identity, version/digest, tenant/owner scope and classification.

## Compiler stages

1. **Ingest and normalize** — resolve source identity, structure, permissions and freshness.
2. **Semantic decomposition** — identify actors, objects, decisions, preconditions, outputs and exception paths.
3. **Process reconstruction** — create candidate workflow graph including waits, approvals, compensations and evidence points.
4. **Skill resolution** — bind existing qualified skills; generate candidates only when no qualified skill matches.
5. **Tool/connector binding** — resolve versioned operations and fidelity classes.
6. **RBAC/policy binding** — map roles, permission atoms, data classes, target restrictions and approval rules.
7. **I/O/evidence contract generation** — define typed inputs, outputs and proof required for completion.
8. **Evaluation generation** — positive, adversarial, recovery and compatibility cases.
9. **Qualification** — execute pack tests using normal WorkGraph/runtime infrastructure.
10. **Publish** — store immutable pack version and dependencies in registry.

## Runtime resolution

Installing a pack never copies ambient credentials or authority. At work admission, control/runtime resolve pack version, compatible skill/tool versions and current user's allowed CapabilitySnapshot. Missing permissions or incompatible connector versions produce a typed admission failure.

## Updates

A source/API/policy change creates a candidate new pack version and impact analysis. It never mutates a published version in place. Historical runs retain the exact pack/skill/tool versions they used.
