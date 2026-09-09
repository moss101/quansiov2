# 41 — Security dependency order

Security is introduced at the first dependent boundary rather than deferred to a final hardening phase.

1. Authenticated tenant/session authority precedes authoritative commands.
2. Foundational immutable CapabilitySnapshot precedes agent/worker/model/tool/machine admission.
3. Model privacy/residency enforcement precedes real provider qualification.
4. Argument-bound policy, destination-aware privacy, credential brokerage and behavior-sequence guards precede consequential effects.
5. Effect Ledger and scoped approval precede connector/browser consequential actuation.
6. Lease/generation/fence enforcement precedes guest or endpoint actuation.
7. Tenant-isolation adversarial tests and build/artifact provenance are repeated at production qualification.

Later security milestones may strengthen controls but cannot be the first implementation of a prerequisite used by an earlier feature.
