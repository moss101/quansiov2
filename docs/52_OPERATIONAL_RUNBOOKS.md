# 52 — Operational runbooks required before production

Create and qualify runbooks for:

1. API/control/runtime partial outage and safe traffic drain.
2. Database failover and RecoveryConsistencyPoint validation.
3. Durable event transport outage/backlog and outbox catch-up.
4. Model provider outage, route disablement and usage reconciliation.
5. Connector outage/webhook backlog and consequential-effect UNKNOWN handling.
6. Worker pool exhaustion and admission backpressure.
7. Machine target unhealthy/migration/restore and generation advance.
8. Browser fleet degradation and human-session preservation.
9. Credential compromise/revocation without exposing secret material.
10. Cross-tenant incident containment and evidence preservation.
11. Artifact/object-store restore and digest verification.
12. Skill or Business Capability emergency disable/rollback.
13. Automation scheduler outage and missed-fire policy handling.
14. Candidate canary rollback and production rollback.
15. Support-profile disablement when qualification no longer holds.

Each runbook names owner/on-call, trigger signals, containment steps, commands/tools, data/effect safety checks, rollback/recovery, communication and post-incident evidence. Runbooks are exercised during qualification; existence of Markdown alone is not acceptance.
