# Tools — Canonical Tool Registry

Every executable tool operation has one versioned contract containing input/output schema, semantic effect class, fidelity, required capability, policy requirements, timeout, idempotency and evidence expectations.

Fidelity classes: `LOSSLESS`, `LOSSLESS_WITH_CONSTRAINTS`, `BEST_EFFORT_DEGRADING`, `IRREVERSIBLE`, `HUMAN_ONLY`, `UNSUPPORTED`.

Effect classes: `OBSERVATIONAL`, `NON_CONSEQUENTIAL`, `CONSEQUENTIAL`, `HIGH_RISK`, `SEMANTICALLY_CLASSIFIED`.

A low-level browser/computer action never bypasses semantic classification. If its real outcome sends, publishes, purchases, deletes, modifies protected state or uploads protected information, it enters the canonical consequential-effect path before actuation.
