# 50 — CI and real-environment blueprint

## Pipeline stages

```text
authority-check
  → generated-contract/build check
  → unit/static/security scan
  → migration/contract tests
  → durable integration environment
  → runtime/effect integration
  → real provider/browser/machine/connector suites as mapped
  → E2E vertical slices
  → load/DR/security qualification
  → immutable candidate build
  → candidate-bound qualification
  → canary/rollback
```

Blocking stages cannot be converted to warnings or `|| true`. A flaky test remains a failure until root-caused; retries may collect diagnostics but cannot turn an unexplained first failure into release PASS.

## Integration environment

Provision isolated identities for PostgreSQL, durable event transport, Redis/lease store and object storage. Seed only through migrations/fixtures. Health and teardown are recorded. Integration runs may not substitute in-memory stores for durability requirements.

## External qualification

Provider, browser, machine and connector suites use test/sandbox accounts or isolated real accounts where available. Secrets are injected by CI/environment secret management and never committed. If a required boundary is unavailable, produce `BLOCKED_REAL_BOUNDARY`, not a fake success.

## Candidate build

Build once from a reachable commit. Record source commit, dependency lock digests, container/binary digests, migration-set digest, configuration digest and support-selection digest. Candidate qualification, canary and production promotion all refer to those exact identities.

## Test reports

Each report lists exact assertion IDs and artifact identities. Completion evidence references the report by digest. The evidence validator independently checks repository reachability, report result, assertion coverage and artifact identity.
