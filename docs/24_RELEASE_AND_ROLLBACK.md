# 24 — Release, canary and rollback

```text
CANDIDATE_CREATED
      ↓
CANDIDATE_QUALIFIED
      ↓
CANARY_DEPLOYED
      ↓
CANARY_QUALIFIED
      ↓
GO_APPROVED
      ↓
READINESS_EVIDENCE_SEALED
      ↓
GATE-M14
      ↓
PRODUCTION_READY
      ↓
separate authorized promotion
      ↓
PRODUCTION_RELEASED
```

Only `GATE-M14` writes `PRODUCTION_READY`. `REL-006` only records `READINESS_EVIDENCE_SEALED`. A rebuild, source/config/migration/support-selection change creates a new candidate; qualification reports are candidate-bound and cannot be transferred.

Canary rollback is a blocking qualification activity. Database changes follow expand/contract or another explicitly reversible strategy. Rollback must preserve already committed external effect history and must never treat effect rollback as equivalent to infrastructure rollback.
