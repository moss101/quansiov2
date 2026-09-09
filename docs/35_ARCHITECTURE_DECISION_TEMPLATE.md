# 35 — Architecture decision template

```text
Decision ID:
Owner:
Status: PROPOSED | ACCEPTED | REJECTED | RETIRED
Context:
Problem:
Decision:
Alternatives considered:
Affected architectural invariants:
Affected canonical owners/schemas/wiring:
Threat/privacy/tenant impact:
Data migration/compatibility impact:
Rollback/reversal plan:
Testing/qualification impact:
Review trigger/date:
```

Decision records do not mark implementation tasks complete. A decision that changes canonical registry truth must update the registry/source and regenerate all reading views.
