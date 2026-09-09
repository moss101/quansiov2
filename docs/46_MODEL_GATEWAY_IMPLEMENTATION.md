# 46 — Model gateway implementation contract

## Admission pipeline

```text
Runtime step
  → ContextProjection
  → CapabilityDemand
  → capability/policy/residency/budget validation
  → deterministic route decision
  → usage reservation
  → ModelRequestEnvelope
  → provider adapter
  → canonical ModelEvent stream
  → usage settlement
```

No client/worker/skill/connector can invoke a provider outside this path.

## Provider adapter interface

A provider adapter implements only protocol translation:

```text
validate_profile(profile)
start(request_envelope) -> provider_stream_handle
translate_event(provider_event) -> ModelEvent | internal-noop
cancel(cancellation_id)
query/settle_usage(request_id) -> usage record
classify_provider_error(error) -> retryability/failure class
```

It receives a normalized request, not unrestricted task state. Credentials are resolved inside the gateway through server-side secret handles.

## Routing

Routing input is a versioned CapabilityDemand plus allowed model catalog, policy, residency, provider health and budget. The decision produces `route_decision_id`, selected `model_profile_id`, catalog revision and reason codes. A provider/model is never selected if it violates an admission constraint even if it scores better on capability.

## Streaming state

Canonical model events use monotonic sequence and exactly one terminal state. Provider-specific aliases are translated in the adapter. Duplicate provider deltas are deduplicated when the provider offers identity; otherwise gateway sequencing and persisted stream state prevent duplicate downstream application.

## Cancellation and usage

Cancellation marks the request cancellation state and attempts provider cancellation. The usage reservation is not released as zero immediately: it enters settlement until the provider's final/late usage is known or the profile-specific settlement deadline expires. Late charges/credits are append-only adjustments.

## Failover

Automatic failover is allowed only before a consequential downstream interpretation depends on ambiguous partial model output, or when the task contract explicitly permits restarting with a new request identity. A provider error cannot cause two model outputs to be presented as one continuous request without explicit lineage.

## Privacy

Before provider egress, content classification and destination/residency policy decide allow/redact/deny. The denied-path qualification captures outbound bytes at the gateway boundary and proves protected content was not transmitted.
