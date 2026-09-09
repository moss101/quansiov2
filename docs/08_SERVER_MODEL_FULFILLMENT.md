# 08 — Server-side model fulfillment

All provider communication flows through `quansio-model-gateway`.

## Admission path
`runtime step → capability/context/budget/privacy constraints → deterministic route decision → ModelRequestEnvelope → provider adapter → ModelEvent stream → runtime`

No mandatory model call may exist solely to choose another model.

## Streaming contract
`MODEL_STARTED` occurs once before deltas. Valid intermediate events: `OUTPUT_DELTA`, `TOOL_PROPOSAL`, `USAGE_DELTA`. Exactly one terminal event: `MODEL_COMPLETED`, `MODEL_CANCELLED`, `MODEL_FAILED`. Sequences are monotonic; post-terminal events are invalid.

## Usage/budget
Reserve budget before provider start. Streaming/final usage settles against the same reservation. Cancellation does not immediately free uncertain usage: state can remain `SETTLING_PROVIDER_USAGE` until final provider usage arrives. Duplicate late usage is idempotent; corrections are append-only adjustments.

## Privacy/residency
Classify context before provider egress. The gateway enforces destination/residency/policy and must prove zero protected bytes leave on denial. Provider adapters do not synthesize absent policy/budget/provenance fields.

## Qualification
An enabled model profile must exercise a real request, stream, cancellation, usage, malformed response and outage/failover behavior using exact deployed adapter/configuration artifacts.
