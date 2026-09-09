# 51 — Threat model and abuse cases

The implementation threat model must cover at least:

- forged tenant/user/workspace identity from clients or webhooks;
- stale/expanded CapabilitySnapshot;
- policy/approval TOCTOU and argument mutation after approval;
- low-level browser actions hiding a consequential semantic effect;
- credential leakage into model context, guest environment, logs or artifacts;
- prompt/tool injection attempting authority expansion;
- worker/endpoint replay after lease/generation/fence changes;
- duplicate delivery causing duplicate payment/message/delete;
- ambiguous external timeout followed by unsafe retry;
- cross-tenant object IDs, cache keys, event subjects, search indexes and artifacts;
- malicious skill/capability package dependency or self-promotion attempt;
- provider/connector webhook spoofing and duplicate delivery;
- sandbox escape, protected-path read/write and internal-network reachability;
- browser takeover race between agent and human controller;
- model/data residency violation;
- stale knowledge synthesis after fork/revert/source change;
- poisoned research source/evidence mismatch;
- compromised build artifact or candidate substitution;
- operator/admin misuse of RBAC/policy/support settings;
- backup restore that replays committed effects.

Every threat maps to preventive controls, detection telemetry, negative tests and recovery/incident handling. Security-critical control failures fail closed.
