# Quansio V9 Final Implementation Authority

**Schema revision:** `9.0.0`

This directory is the complete implementation authority for Quansio. It is intended for direct use by implementation agents and human engineers. The authority is self-contained: architecture, product behavior, service ownership, canonical contracts, machine-readable requirements/tasks, dependency graph, wiring, support matrix, qualification, release gates, source-completeness checks and evidence validation are all included.

## Product contract

Quansio is one governed platform combining:

1. **Persistent autonomous work** — durable digital teammates, ephemeral workers, collaboration, routines, browser/computer execution, connectors, approvals and multi-device continuation.
2. **Evidence-first intelligence** — typed programmable research, wide/deep discovery, entity resolution, verification, provenance, freshness and reproducible scoring.
3. **Quansio for Business** — Business Capability Packs and a Capability Compiler that turn authoritative enterprise material into governed, evaluated executable capabilities.
4. **Controlled Skill Evolution** — evidence-backed candidate skill extraction, isolated evaluation, governed promotion, versioning and rollback.

All four outcomes execute through the same canonical runtime, policy, tool, effect, evidence, knowledge, machine and recovery primitives.

## Start here

Read `AGENTS.md`, `HANDOFF.md`, the master dossier, `docs/19_IMPLEMENTATION_PLAN.md`, `docs/20_ATOMIC_TASK_REGISTRY.md`, `docs/21_WIRING.md`, `docs/26_REAL_IMPLEMENTATION_COMPLETION_CONTRACT.md`, `docs/27_TEST_VERIFICATION_AND_EVIDENCE.md`, all canonical schemas/registries and the implementation kickoff prompt.

Run:

```sh
python3 scripts/validate_authority.py
python3 scripts/validate_contracts.py
python3 scripts/self_test_validators.py
```

Counts are generated from canonical registries: **135 tasks, 111 requirements, 43 canonical schemas**.
