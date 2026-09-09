# 40 — Contract conformance fixtures

Every canonical schema has a positive fixture under `tests/fixtures/valid/` and a corresponding negative fixture under `tests/fixtures/invalid/`. Positive fixtures must validate and negative fixtures must fail. Coverage equality between the schema registry and both fixture directories is itself release-blocking. The fixture set explicitly includes:

- model request identity/generation/routing/budget/context fields;
- canonical `ModelEvent.event_type` vocabulary;
- endpoint generation, lease, fence, capability, policy, effect and approval scope;
- typed non-executable SearchProgram predicates;
- reproducible implementation evidence and blocking assertion results;
- immutable graph and capability identities;
- support/qualification selection and release ownership.

A validator that accepts a deliberately invalid fixture fails qualification even if all valid fixtures pass.
