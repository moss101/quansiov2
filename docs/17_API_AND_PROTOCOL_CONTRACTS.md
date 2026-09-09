# 17 — API and protocol contracts

All canonical wire/durable contracts carry `schema_revision: "9.0.0"` and reject missing/unknown revisions unless a deliberately implemented compatibility adapter validates all required authority fields from trusted state.

## Command rules
- Server resolves authenticated actor/tenant/workspace identity.
- Client supplies command-specific arguments and idempotency identity, not canonical completion/effect truth.
- Commands return accepted/rejected plus stable command/run identifiers; long work is observed through events.

## Versioning
Breaking contract change creates a new schema revision, fixtures, generated bindings, compatibility decision and migration tests. Never accept an older incomplete envelope by inventing approval, capability, policy, budget, generation, tenant or provenance fields.

## Fixtures
Each critical contract family has valid fixtures plus invalid fixtures for omitted required identity/policy/generation/scope fields. Contract CI validates fixtures against the exact registered schema.
