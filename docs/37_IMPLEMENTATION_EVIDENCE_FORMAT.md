# 37 — Implementation evidence format

Completion is reproducibility-based, not signature-based.

`VerificationReport` contains task, repository/commit/protected ref, CI run/pipeline identity, environment/configuration digest, PASS/FAIL/BLOCKED state, assertion results, artifact identities/digests/verification method, real-boundary state and execution time.

`ImplementationEvidence` contains exact requirement IDs, task assertion IDs and requirement assertion IDs; repository commit; report path/digest; artifact digests; real-boundary and rollback state.

Validator rules:
1. task exists;
2. requirement IDs exactly equal task requirement IDs;
3. task assertion IDs exactly equal blocking task assertions;
4. requirement assertion IDs exactly equal linked requirement assertion IDs;
5. commit exists and is reachable from configured qualification ref;
6. report exists and digest matches;
7. report belongs to the same task/commit/environment;
8. every blocking assertion PASS for completion;
9. local artifacts hash to declared digests; remote artifacts require digest lookup or trusted build attestation receipt;
10. `real_boundary=true` when task requires it;
11. `BLOCKED_REAL_BOUNDARY` never closes work.
