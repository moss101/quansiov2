# 35 — Architecture decision record

```text
Decision ID: ADR-0002
Owner: architecture
Status: ACCEPTED
Context: The authority fixes canonical owners, contracts and stores but
leaves server language choice open ("Equivalent language-specific
organization is acceptable", doc 44). Doc 39 names the Python/FastAPI
migration baseline; doc 43 fixes Electron + React + TypeScript clients; doc
45 fixes PostgreSQL as authoritative store with a Redis-equivalent
non-authoritative lease/cache store. The implementation repository starts
empty of application code; ENV-001 requires a fixed stack.
Problem: Choose and freeze the implementation technology stack and repository
layout for the whole DAG before foundation work begins.
Decision: Python 3.12 server runtime; per-owner packages under
`quansio/<owner>/`, deployables under `services/<owner>/main.py`, FastAPI
HTTP surfaces. PostgreSQL (compose-provisioned real server) is the single
authoritative relational store; per-area schema ownership is tracked from
DAT-002. Redis is restricted to non-authoritative coordination (leases, rate
limits, reconstruction-safe cache). MinIO (S3 API) is the immutable
artifact/evidence object store owned by quansio-artifact. Clients are
TypeScript/React per doc 43 in `clients/`. Canonical contract bindings are
generated from `schemas/*.schema.json` into `generated/`; hand-written
competing DTOs are forbidden. pytest qualifies acceptance suites.
Alternatives considered: Go monorepo (doc 44 layout is Go-shaped but the
authority explicitly permits equivalent organization; Python matches the
migration baseline and schema/model ecosystem); SQLite/in-process databases
(forbidden by ENV-001 real-boundary requirements); Node-only full stack
(splits from the Python migration baseline without offsetting benefit).
Affected architectural invariants: none weakened; supports one-core
ownership, evidence reproducibility and server-side-only model fulfillment.
Affected canonical owners/schemas/wiring: all canonical services registered
with packages and deployables; registry decision references point to this
record.
Threat/privacy/tenant impact: Python dependency supply chain is a threat
surface; dependencies are pinned via `pyproject.toml` and lockfiles, vendored
trees are excluded from payload scans, and provenance is qualified by
SEC-007.
Data migration/compatibility impact: Additive (no prior application code).
Rollback/reversal plan: Trivial before DAT-002 creates durable schema;
afterwards rollback follows the migration down-procedures defined by DAT-002.
Testing/qualification impact: All qualification suites run under this stack;
ENV-001 provisions real PostgreSQL/Redis/MinIO instances.
Review trigger/date: Introduction of any second server-side language runtime
or a required capability missing from the stack; review 2026-12-10.
```
