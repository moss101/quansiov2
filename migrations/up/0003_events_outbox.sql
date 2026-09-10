-- 0003: canonical RuntimeEvent log and transactional outbox (DAT-003/DAT-004).
-- The events table is the durable event transport; the outbox guarantees
-- state mutation and event publication share one transaction.
BEGIN;

CREATE TABLE runtime_events (
    tenant_id      UUID NOT NULL,
    workspace_id   UUID NOT NULL,
    run_id         UUID NOT NULL,
    sequence       BIGINT NOT NULL CHECK (sequence > 0),
    event_id       UUID NOT NULL,
    event_type     TEXT NOT NULL,
    producer       TEXT NOT NULL,
    generation     BIGINT NOT NULL DEFAULT 0,
    causal_parents UUID[] NOT NULL DEFAULT '{}',
    payload        JSONB NOT NULL,
    committed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, event_id),
    UNIQUE (run_id, sequence)
);
CREATE INDEX idx_events_replay ON runtime_events(tenant_id, run_id, sequence);

-- Delivery cursors: idempotent projection/consumer replay positions.
CREATE TABLE event_cursors (
    tenant_id    UUID NOT NULL,
    consumer     TEXT NOT NULL,
    run_id       UUID NOT NULL,
    last_sequence BIGINT NOT NULL DEFAULT 0,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, consumer, run_id)
);

-- Transactional outbox: rows written in the same transaction as the
-- authoritative mutation they announce.
CREATE TABLE event_outbox (
    outbox_id   BIGSERIAL PRIMARY KEY,
    tenant_id   UUID NOT NULL,
    event_id    UUID NOT NULL,
    published_at TIMESTAMPTZ,
    attempts    INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, event_id) REFERENCES runtime_events(tenant_id, event_id)
);
CREATE INDEX idx_outbox_unpublished ON event_outbox(outbox_id) WHERE published_at IS NULL;
COMMIT;
