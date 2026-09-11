# 35 — Architecture decision record

```text
Decision ID: ADR-0004
Owner: architecture
Status: ACCEPTED
Context: The canonical ownership registry (ADR-0002) declared twelve
canonical services, but several deployables exposed only health endpoints
while their domain logic lived in packages owned by other services
(notification delivery inside quansio/context/collaboration.py; connector
mediation and webhook ingress inside quansio/control/connectors.py), the
notification deployable was missing entirely, no client surfaces were
implemented (all client paths registered as planned), and public command
admission returned an envelope without durable run truth, which forced
clients to substitute command ids for run ids.
Problem: Reconcile the deployed tree with the canonical ownership model
without a second orchestrator, second task store or alternate effect path,
and give every canonical service a real HTTP surface with server-resolved
identity, so the command-to-result journey, client surfaces and deployment
operations behave as the canonical tasks (DAT-001, RUN-001..008, COL-003,
EXT-002/003, MAC-003/005, SRE-004/005, REL-001..008, UX-001..008) demand.
Decision:
1. Each canonical service exposes its package behavior through a
   `quansio/<owner>/app.py` `create_app` factory consumed by a thin
   `services/<owner>/main.py` entrypoint. All routes resolve identity from
   a quansio-control bearer session; no route trusts client-supplied
   authoritative identity fields.
2. Notification delivery moves to the canonical package `quansio/notify`
   (owner quansio-notify); `quansio/context/collaboration.py` re-exports it
   for compatibility. Connector mediation and webhook ingress move to the
   canonical package `quansio/integration_broker`; `quansio/control/
   connectors.py` keeps the ToolRegistry (control-owned) and re-exports the
   moved classes.
3. Public commands become durably admitted by the runtime: migration 0021
   adds the runtime-owned `commands` store; the runtime exposes
   `POST /v9/admissions` (idempotent by tenant + idempotency key, creating
   the run and emitting run.started); quansio-api forwards admitted
   commands with the caller's own bearer session and returns the produced
   run_id. The API holds no command or run truth of its own.
4. Browser-facing services permit configured cross-origin static origins
   (QUANSIO_WEB_ORIGINS; localhost static servers plus the literal null
   origin for the Electron file:// shell by default). No wildcard origins.
5. Run reads and status updates apply the same workspace filter as run
   listing (runs are workspace aggregates).
6. Supported clients are thin projections implemented as clients/cli
   (packaged), clients/web, clients/desktop (Electron around the web
   projection) and clients/mobile (attention PWA), sharing clients/pyapp;
   they own no execution, model, effect or task authority.
7. Provider-credential hygiene is preserved outside the gateway: no
   module outside quansio/model_gateway carries provider credential path
   literals; the broker-mediated connector transport carries exchanged
   handle material in the X-Quansio-Handle contract header.
Alternatives considered: keeping logic in borrowing packages with
forwarding HTTP calls between services (rejected: leaves ownership
misalignment and adds hop latency without fixing identity of code);
persisting commands in the API service (rejected: client-owned task truth
is forbidden and duplicates runtime admission); wildcard CORS (rejected:
ambiguous trust boundary for credential-bearing requests); requiring
sessions only at quansio-api and trusting service-to-service calls without
identity (rejected: every canonical surface must re-resolve identity from
the control authority).
Affected architectural invariants: canonical-owner rule (one owner per
behavior); one-core rule (no second task store — the commands store is the
runtime's admission truth, not a parallel orchestrator); real
implementation rule (no simulated provider success; drills, canary and
load qualifications execute real operations).
Affected canonical owners/schemas/wiring: quansio-notify,
quansio-integration-broker, quansio-control (registry kept), quansio-api,
quansio-runtime (admission), all twelve deployable surfaces; migration
0021 (commands); RuntimeEvent producers unchanged; owners registry entries
flipped from planned to present with the same decision lineage.
Threat/privacy/tenant impact: identity is re-resolved per service from
control; workspace scoping closes same-tenant cross-workspace reads;
ambient-secret refusal and environment sanitization demonstrated at the
guest boundary; CORS is an explicit deployment-configured origin list.
Data migration/compatibility impact: migration 0021 is additive; the
commands store back-fills nothing and requires no data migration;
re-exports preserve existing import paths so no consumer breaks.
Rollback/reversal plan: retire this record, restore the prior registry
statuses, drop migration 0021 via its down migration and re-point the API
at envelope-only admission in the same change; the evidence validator and
contract gate fail until the tree is consistent again.
Testing/qualification impact: new service-surface suite (tests/services),
command-to-result journey (tests/qa/test_command_journey.py), real
backup/restore drill, measured-load qualification, real canary/rollback
operations, promotion-of-current-commit test (tests/release/
test_promotion_operations.py), browser qualification transcripts for web
and mobile surfaces; all bound into the canonical assertion maps and
re-recorded.
Review trigger/date: review on any new canonical client surface, any
change to the admission chain, or at the next release candidate;
initial review date 2026-12-11.
```
