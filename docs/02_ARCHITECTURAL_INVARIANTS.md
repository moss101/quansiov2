# 02 — Architectural invariants

1. **One runtime authority.** WorkGraph/AgentGraph/StateGraph plus GraphTransaction own task execution state.
2. **Model proposes; runtime owns reality.** Model output can propose tools/plans/content but cannot directly mutate authoritative state or external systems.
3. **One effect path.** Consequential actions require semantic operation, capability, policy/privacy/security, approval where needed, EffectRecord, actuation, receipt/evidence and reconciliation.
4. **Memory is not recovery.** Canonical events, protocol state, checkpoints, execution generations and effect reconciliation restore execution.
5. **Clients are projections.** Desktop/web/mobile/CLI cannot become task/effect/approval/model authority.
6. **Server-side model fulfillment.** Provider credentials and provider calls live only in the model gateway trust boundary.
7. **One Knowledge Fabric.** Enterprise/user/research/successful-work/engineering knowledge share one semantic store/query model with provenance; protocol and recovery state remain separate.
8. **One Tool Registry.** Research, business, automation and general work resolve the same typed operations.
9. **Authority narrows.** Child capabilities, budgets, target scope and credentials are strict subsets of admitted parent authority.
10. **No superficial completion.** Interfaces/UI/tests without real production wiring do not satisfy acceptance.
