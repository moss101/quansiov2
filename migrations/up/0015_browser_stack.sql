-- 0015: browser stack durable state (BRW-001..BRW-008).
BEGIN;
CREATE TABLE browser_sessions (
    tenant_id    UUID NOT NULL,
    workspace_id UUID NOT NULL,
    session_id   UUID NOT NULL,
    target_id    TEXT NOT NULL,
    generation   BIGINT NOT NULL,
    state        TEXT NOT NULL CHECK (state IN ('active','degraded','hibernated','closed')),
    control_holder TEXT,
    control_kind TEXT CHECK (control_kind IN ('agent','human',NULL)),
    page_epoch   BIGINT NOT NULL DEFAULT 1,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, session_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE browser_observations (
    observation_id UUID NOT NULL,
    tenant_id    UUID NOT NULL,
    session_id   UUID NOT NULL,
    run_id       UUID,
    step_id      TEXT,
    page_epoch   BIGINT NOT NULL,
    kind         TEXT NOT NULL CHECK (kind IN ('state','action','result')),
    content      JSONB NOT NULL,
    content_digest TEXT NOT NULL,
    captured_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, observation_id),
    FOREIGN KEY (tenant_id, session_id) REFERENCES browser_sessions(tenant_id, session_id)
);

CREATE TABLE browser_transfers (
    transfer_id  UUID NOT NULL,
    tenant_id    UUID NOT NULL,
    session_id   UUID NOT NULL,
    direction    TEXT NOT NULL CHECK (direction IN ('upload','download')),
    artifact_digest TEXT NOT NULL,
    state        TEXT NOT NULL CHECK (state IN ('granted','interrupted','completed')),
    bytes_done   BIGINT NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, transfer_id),
    FOREIGN KEY (tenant_id, session_id) REFERENCES browser_sessions(tenant_id, session_id)
);
COMMIT;
