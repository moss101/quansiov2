# ADR-0002: Implementation technology stack and repository layout

- **Status:** Accepted
- **Owner:** architecture
- **Date:** 2026-09-10
- **Task context:** GOV-001, GOV-002, ENV-001

## Context

The authority names its canonical owners, contracts and stores but leaves
language choice open ("Equivalent language-specific organization is
acceptable", doc 44). doc 39 references prior Python/FastAPI
tool/provider/context code as the migration baseline; doc 43 fixes Electron +
React + TypeScript for the desktop client; doc 45 fixes PostgreSQL as the
default authoritative store with Redis-equivalent as non-authoritative
lease/cache store. The implementation repository starts empty of application
code, so the stack must be fixed before ENV-001.

## Decision

- **Backend/runtime language:** Python 3.12 (per-owner packages under
  `quansio/<owner>/`, deployables under `services/<owner>/main.py`, FastAPI
  for HTTP surfaces). Canonical imports remain mechanically enforceable via
  the ownership inventory plus package boundaries.
- **Authoritative store:** PostgreSQL (compose-provisioned, real server for
  all durable qualification). Logical per-area schema ownership is tracked in
  the schema ownership registry from DAT-002 onward.
- **Non-authoritative coordination:** Redis (leases, rate limits,
  reconstruction-safe cache only, per DAT-007).
- **Object storage:** MinIO (S3 API) as the immutable artifact/evidence
  boundary owned by `quansio-artifact`.
- **Frontend/clients:** TypeScript/React per doc 43 (desktop Electron shell,
  web client, mobile attention client, thin CLI), built in `clients/`.
- **Generated bindings:** Python dataclasses and TypeScript types generated
  from `schemas/*.schema.json` into `generated/` (GOV-003); hand-written
  competing DTOs are forbidden.
- **Test/verification tooling:** pytest for acceptance suites;
  `scripts/validate_implementation_evidence.py` remains the completion
  validator.

## Alternatives rejected

- Go monorepo (doc 44's layout is Go-shaped): rejected — the authority's
  migration baseline and ecosystem fit (schemas/jsonschema, FastAPI,
  psycopg, model SDKs) favor Python; doc 44 explicitly permits equivalent
  language-specific organization.
- SQLite/in-process DB for qualification: forbidden by ENV-001 (real
  relational boundary required).
- Node-only full-stack: splits the runtime from the authority's
  Python-based migration guidance without offsetting benefit.

## Affected invariants

None weakened; supports one-core (single canonical packages), evidence
(reproducible local + CI qualification), and server-side model fulfillment
(Python gateway boundary).

## Threat impact

Python dependency supply chain is a threat surface: dependencies are pinned
in `pyproject.toml`/lockfile, vendored trees are never scanned as payload,
and SBOM/provenance qualification is covered by SEC-007.

## Migration / rollback

Stack adoption is additive (empty app tree today). Rollback before DAT-002
is trivial; after durable schema exists, rollback follows the migration
down-procedures defined then.

## Review trigger

Any introduction of a second language runtime in the server path, or a
required capability missing from the chosen stack, triggers a new decision.
