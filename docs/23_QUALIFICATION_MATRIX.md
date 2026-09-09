# 23 — Qualification matrix

Blocking suites:

| Suite | Scope |
|---|---|
| Q-AUTH | authority, identity, tenant isolation |
| Q-DATA | durable storage, events, protocol state |
| Q-RUNTIME | graphs, workers, budgets, cancellation/recovery |
| Q-MODEL | server model fulfillment |
| Q-RESEARCH | evidence-first research thresholds |
| Q-EFFECT | policy, approvals, effects/reconciliation |
| Q-MACHINE | worker/machine fabric |
| Q-BROWSER | browser and endpoint control |
| Q-SKILL | knowledge and controlled skill evolution |
| Q-BUSINESS | capability compiler/packs |
| Q-AUTOMATION | schedules/collaboration |
| Q-CLIENT | supported client convergence/accessibility |
| Q-SECURITY | privacy, credentials, sequence guard, tenant isolation |
| Q-DR | recovery consistency, backup/restore |
| Q-LOAD | load, soak, quota, cost and degradation |
| Q-CANARY | candidate/canary/rollback/release |

Every enabled support profile maps to required suites and qualification tasks. Any blocking assertion failure is a suite failure regardless of aggregate pass percentage. Reports bind the exact code/config/environment/artifacts tested.
