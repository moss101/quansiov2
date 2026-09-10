-- 0009: worker admission, child turns, and budget reservations (RUN-004..008).
BEGIN;

-- Turn dispatches: parent fan-out units (RUN-005).
CREATE TABLE turns (
    tenant_id     UUID NOT NULL,
    workspace_id  UUID NOT NULL,
    turn_id       UUID NOT NULL,
    parent_run_id UUID NOT NULL,
    child_agent_id UUID NOT NULL,
    graph_id      UUID,
    status        TEXT NOT NULL CHECK (status IN ('queued','running','succeeded','failed','cancelled','expired')),
    payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
    deadline_at   TIMESTAMPTZ,
    dispatched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    terminal_at   TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, turn_id),
    FOREIGN KEY (tenant_id, parent_run_id) REFERENCES runs(tenant_id, run_id),
    FOREIGN KEY (tenant_id, child_agent_id) REFERENCES agents(tenant_id, agent_id)
);
CREATE INDEX idx_turns_parent ON turns(tenant_id, parent_run_id, status);

-- Child turn outcomes: incremental results, idempotent by (turn, delivery).
CREATE TABLE turn_outcomes (
    tenant_id    UUID NOT NULL,
    turn_id      UUID NOT NULL,
    delivery_id  UUID NOT NULL,
    partial      BOOLEAN NOT NULL DEFAULT false,
    result       JSONB NOT NULL,
    received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, turn_id, delivery_id),
    FOREIGN KEY (tenant_id, turn_id) REFERENCES turns(tenant_id, turn_id)
);

-- Hierarchical budget reservations (RUN-007): frozen at parent ceiling.
CREATE TABLE budget_reservations (
    tenant_id        UUID NOT NULL,
    reservation_id   UUID NOT NULL,
    parent_run_id    UUID NOT NULL,
    idempotency_key  TEXT NOT NULL,
    amount_cents     BIGINT NOT NULL CHECK (amount_cents > 0),
    status           TEXT NOT NULL CHECK (status IN ('reserved','settling','settled','released','expired')),
    reserved_cents   BIGINT NOT NULL,
    committed_cents  BIGINT NOT NULL DEFAULT 0,
    worker_generation BIGINT NOT NULL DEFAULT 1,
    worker_agent_id   UUID,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, reservation_id),
    UNIQUE (tenant_id, parent_run_id, idempotency_key),
    FOREIGN KEY (tenant_id, parent_run_id) REFERENCES runs(tenant_id, run_id),
    CONSTRAINT committed_lte_reserved CHECK (committed_cents <= reserved_cents)
);
COMMIT;
