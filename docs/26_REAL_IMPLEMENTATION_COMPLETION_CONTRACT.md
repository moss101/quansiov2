# 26 — Real implementation completion contract

A task is complete only when production behavior exists on its canonical path and every blocking assertion has valid executed evidence.

## Not completion
- compiling interfaces or empty handlers
- UI without the backend/runtime path
- mocks/fakes replacing a required real boundary
- process-local state replacing required durable state
- simulated provider/connector success
- placeholder branches or swallowed exceptions returning success
- skipped/quarantined blocking tests
- hand-edited PASS state

## Evidence
Completion evidence binds exact task, requirements, task/requirement assertion IDs, repository identity, reachable commit, verification report digest/content, environment/configuration, artifact digests and real-boundary proof when required. Cryptographic report signatures are not required. The evidence validator independently reads and verifies the report/artifacts/repository rather than trusting an outer PASS label.

`BLOCKED_REAL_BOUNDARY` documents an unavailable dependency and exits non-success for closure. It records boundary, reason, owner, attempted verification and unblock condition.
