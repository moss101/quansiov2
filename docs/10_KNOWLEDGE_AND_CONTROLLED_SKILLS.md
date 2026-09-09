# 10 — Knowledge Fabric and Controlled Skill Evolution

Knowledge candidates carry provenance, evidence, source epoch, confidence, validity and conflicts. Asynchronous synthesis commits only if relevant source/task epochs still match; stale results are rejected but retained diagnostically.

Knowledge Fabric stores semantic knowledge. It does not store the authoritative live run protocol and cannot be used to reconstruct missing execution state.

## Skill lifecycle
`authoritative material → candidate → static/security checks → isolated evaluation → regression → qualified version → registry → task-scoped materialization`

Promotion is a separate governed control-plane operation. Skill helpers cannot mutate promotion, policy or capability authority. Running tasks remain pinned to their admitted skill version; rollback changes resolution for new work.
