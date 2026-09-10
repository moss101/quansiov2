-- 0017: business capability packs, tool registry, integration broker,
-- webhook ingress (BUS-001..005, EXT-001..003).
BEGIN;
CREATE TABLE capability_packs (
    tenant_id       UUID NOT NULL,
    pack_id         TEXT NOT NULL,
    version         INT NOT NULL,
    identity        JSONB NOT NULL,
    requirements    JSONB NOT NULL DEFAULT '{}'::jsonb,
    rbac            JSONB NOT NULL DEFAULT '{}'::jsonb,
    policy          JSONB NOT NULL DEFAULT '{}'::jsonb,
    approvals       JSONB NOT NULL DEFAULT '[]'::jsonb,
    workflows       JSONB NOT NULL DEFAULT '[]'::jsonb,
    io_contract     JSONB NOT NULL DEFAULT '{}'::jsonb,
    evidence_policy JSONB NOT NULL DEFAULT '{}'::jsonb,
    evaluations     JSONB NOT NULL DEFAULT '[]'::jsonb,
    compatibility   JSONB NOT NULL DEFAULT '{}'::jsonb,
    lifecycle       TEXT NOT NULL CHECK (lifecycle IN ('draft','compiled','bound','qualified','published','rolled_back')),
    rollback_version INT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, pack_id, version),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE pack_sources (
    source_id   BIGSERIAL PRIMARY KEY,
    tenant_id   UUID NOT NULL,
    pack_id     TEXT NOT NULL,
    version     INT NOT NULL,
    source_ref  TEXT NOT NULL,
    authority   TEXT NOT NULL CHECK (authority IN ('authoritative','supplementary','contradicted')),
    content_digest TEXT NOT NULL,
    components  JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE tool_operations (
    tenant_id       UUID NOT NULL,
    operation_name  TEXT NOT NULL,
    version         INT NOT NULL,
    schema          JSONB NOT NULL,
    effect_class    TEXT NOT NULL CHECK (effect_class IN ('harmless','state_changing','consequential','degrading')),
    fidelity_class  TEXT NOT NULL CHECK (fidelity_class IN ('lossless','filtered','lossy','best_effort')),
    capability_need TEXT NOT NULL,
    policy_need     TEXT NOT NULL,
    timeout_ms      INT NOT NULL,
    idempotent      BOOLEAN NOT NULL,
    evidence_contract TEXT NOT NULL,
    lifecycle       TEXT NOT NULL DEFAULT 'active' CHECK (lifecycle IN ('active','deprecated')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, operation_name, version),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE pack_bindings (
    binding_id  BIGSERIAL PRIMARY KEY,
    tenant_id   UUID NOT NULL,
    pack_id     TEXT NOT NULL,
    version     INT NOT NULL,
    step_ref    TEXT NOT NULL,
    operation_name TEXT NOT NULL,
    operation_version INT NOT NULL,
    role        TEXT NOT NULL,
    permission  TEXT NOT NULL,
    policy_rule TEXT NOT NULL,
    approval_required BOOLEAN NOT NULL,
    evidence_requirement TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE webhook_ingress (
    tenant_id     UUID NOT NULL,
    webhook_id    UUID NOT NULL,
    source_name   TEXT NOT NULL,
    signature_valid BOOLEAN NOT NULL,
    event_identity TEXT NOT NULL UNIQUE,
    payload       JSONB NOT NULL,
    work_ref      TEXT,
    state         TEXT NOT NULL CHECK (state IN ('received','work_created')),
    received_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, webhook_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
COMMIT;
