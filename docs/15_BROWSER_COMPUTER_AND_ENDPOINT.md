# 15 — Browser, computer and personal endpoint control

One canonical browser/computer stack serves research, general work, automation and business capabilities.

## Browser control preference
Prefer structured page/accessibility/network/session state for deterministic actions and extraction. Visual interpretation is a fallback for content/control not adequately represented structurally.

## Live session
The same browser session is shown to the user. Viewer/controller identity is explicit. Human takeover obtains controller authority; return of control requires the agent to re-observe current state before continuing.

## Semantic browser effects
`click`, `type`, `select`, `submit` are actuator primitives, not effect classes. Semantic outcome is determined before consequential actuation. Purchases, sends, publications, destructive writes and protected uploads require the normal policy/approval/effect path.

## Endpoint relay
`EndpointActionEnvelope` binds endpoint/target, execution generation, lease, fence, capability, policy, effect, delivery attempt, idempotency, operation/schema revision, expiry and approval receipt/scope when required. Stale generation/fence, expired action or mismatched approval scope is rejected before endpoint actuation. ACK/redelivery returns the original result for a completed idempotency identity.
