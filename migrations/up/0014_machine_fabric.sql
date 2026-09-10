-- 0014: machine fabric durable state (MAC-001..MAC-008).
BEGIN;

CREATE TABLE execution_targets (
    tenant_id        UUID NOT NULL,
    target_id        TEXT NOT NULL,
    target_type      TEXT NOT NULL CHECK (target_type IN ('fs','terminal','browser','computer','private')),
    lifecycle        TEXT NOT NULL CHECK (lifecycle IN ('registered','enabled','disabled','retired')),
    execution_generation BIGINT NOT NULL DEFAULT 1,
    support_profile  TEXT NOT NULL,
    health_identity  TEXT NOT NULL,
    last_heartbeat   TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, target_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE target_events (
    event_id   BIGSERIAL PRIMARY KEY,
    tenant_id  UUID NOT NULL,
    target_id  TEXT NOT NULL,
    kind       TEXT NOT NULL,
    detail     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, target_id) REFERENCES execution_targets(tenant_id, target_id)
);

CREATE TABLE fence_counters (
    tenant_id   UUID NOT NULL,
    target_id   TEXT NOT NULL,
    fence_token BIGINT NOT NULL,
    PRIMARY KEY (tenant_id, target_id),
    FOREIGN KEY (tenant_id, target_id) REFERENCES execution_targets(tenant_id, target_id)
);

CREATE TABLE target_leases (
    tenant_id   UUID NOT NULL,
    target_id   TEXT NOT NULL,
    fence_token BIGINT NOT NULL,
    generation  BIGINT NOT NULL,
    holder      TEXT NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, target_id),
    FOREIGN KEY (tenant_id, target_id) REFERENCES execution_targets(tenant_id, target_id)
);

CREATE TABLE worker_deliveries (
    tenant_id        UUID NOT NULL,
    delivery_id      UUID NOT NULL,
    target_id        TEXT NOT NULL,
    operation        TEXT NOT NULL,
    arguments        JSONB NOT NULL DEFAULT '{}'::jsonb,
    idempotency_key  TEXT NOT NULL,
    attempt          INT NOT NULL DEFAULT 0,
    expires_at       TIMESTAMPTZ NOT NULL,
    status           TEXT NOT NULL CHECK (status IN ('pending','delivered','acked','expired')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, delivery_id),
    FOREIGN KEY (tenant_id, target_id) REFERENCES execution_targets(tenant_id, target_id)
);

CREATE TABLE worker_results (
    tenant_id       UUID NOT NULL,
    idempotency_key TEXT NOT NULL,
    result          JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, idempotency_key),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE task_environments (
    tenant_id    UUID NOT NULL,
    task_id      TEXT NOT NULL,
    root_path    TEXT NOT NULL,
    declared_inputs JSONB NOT NULL DEFAULT '[]'::jsonb,
    state        TEXT NOT NULL CHECK (state IN ('provisioned','destroyed')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, task_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE workspace_computers (
    tenant_id    UUID NOT NULL,
    workspace_id UUID NOT NULL,
    computer_id  TEXT NOT NULL,
    owner_id     UUID NOT NULL,
    state_path   TEXT NOT NULL,
    lifecycle    TEXT NOT NULL CHECK (lifecycle IN ('active','hibernating','resumed')),
    execution_generation BIGINT NOT NULL DEFAULT 1,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, workspace_id, computer_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE checkpoints (
    tenant_id     UUID NOT NULL,
    checkpoint_id TEXT NOT NULL,
    computer_id   TEXT NOT NULL,
    kind          TEXT NOT NULL CHECK (kind IN ('workspace_only','full_machine')),
    state         TEXT NOT NULL CHECK (state IN ('created','verifying','restorable','failed')),
    references_json JSONB NOT NULL,
    references_digest TEXT NOT NULL,
    restored_generation BIGINT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, checkpoint_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
COMMIT;
