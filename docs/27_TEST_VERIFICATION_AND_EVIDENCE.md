# 27 — Test, verification and evidence matrix

Apply every relevant layer per task: unit, schema, contract, migration, integration, E2E, concurrency, duplicate/idempotency, cancellation, timeout, stale generation/capability, tenant isolation, approval-scope mutation, crash/restart, dependency outage, recovery, security/adversarial, load, DR, rollback and canary.

Real-boundary tasks must use the real class of boundary defined by their task/support profile. A fake can support isolated unit tests but cannot close real provider, browser, machine, durable-store or connector qualification.

## Report rules
- Report status PASS only when every blocking assertion result is PASS.
- Assertion IDs must exactly cover the task plus linked requirement assertion IDs.
- Commit must exist and be reachable from the configured protected qualification ref.
- Local artifact digests are re-hashed; remote artifacts require digest lookup or trusted build attestation receipt.
- If rollback/recovery is required, its assertion/result is blocking.
- Evidence validator has no authority to weaken task requirements.
