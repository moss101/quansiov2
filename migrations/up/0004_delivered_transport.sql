-- 0004: durable delivery surface for the transactional outbox.
-- Delivery insertions are deduplicated by (tenant_id, event_id) so a
-- publisher crash between transport publish and outbox acknowledgement
-- cannot duplicate an event for consumers.
BEGIN;
CREATE TABLE delivered_events (
    tenant_id    UUID NOT NULL,
    event_id     UUID NOT NULL,
    delivered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, event_id)
);
COMMIT;
