# 09 — Context, research and evidence-first intelligence

## SearchProgram
Allowed operators are `SEARCH`, `RETRIEVE`, `FAN_OUT`, `FILTER`, `RANK`, `DEDUPLICATE`, `JOIN`, `EXTRACT`, `RESOLVE_ENTITY`, `VERIFY`, `ITERATE`, `SYNTHESIZE`. Operator inputs/outputs are typed references. Fan-out <=1000; iteration <=20 unless a future schema revision explicitly changes the bound.

Filter/stop predicates are data ASTs using `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `contains`, `in`, `exists`, `and`, `or`, `not`. Executable predicate/code strings are invalid.

## Research record
Separate canonical entity identity, attributes, claims, source refs, freshness, confidence and verification. A citation existing is not proof; verification can independently refetch the source and classify supported/unsupported/stale/inaccessible/conflicting.

## Wide/deep execution
Parallel discovery/enrichment uses durable intermediate result sets, deduplication and explicit cost/time/fan-out limits. Partial results identify missing/error states rather than fabricating completion.

## Blocking quality thresholds
- discovery recall >= 0.90
- entity precision >= 0.95
- claim/attribute precision >= 0.95
- citation support >= 0.98
- freshness compliance >= 0.98
- duplicate rate <= 0.02
- hard completion >= 0.85

The benchmark binds dataset digest, source-policy identity, scorer revision and metric formulas so results are reproducible.
