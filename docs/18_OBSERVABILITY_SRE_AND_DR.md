# 18 — Observability, SRE and disaster recovery

## Correlation
Logs/metrics/traces correlate command, session, run, step, model request, tool operation, effect, worker, target and recovery point. Protected payload content is not emitted merely to improve observability.

## Objectives
- Authenticated command/event API availability: 99.95% monthly.
- Command admission p95: <=500 ms, excluding external provider/tool latency.
- Event projection lag p95: <=2 s under qualified load.
- Warm isolated runtime readiness p95: <=20 s; cold p95: <=60 s for the qualified hosted profile.
- Authoritative state: RPO <=300 s, RTO <=1800 s.
- Evidence/object state: RPO <=900 s, RTO <=3600 s.

## DR
Backups alone are not proof. Restore drills bind RecoveryConsistencyPoint and validate database/events/evidence/snapshots/effects together. Unresolved UNKNOWN effects are reconciled before consequential work reopens.

## Load/degradation
Admission, queueing, fan-out, model usage, worker placement, storage and connector budgets are bounded. Dependency overload triggers explicit backpressure/degradation rather than uncontrolled retry loops or cross-tenant resource theft.
