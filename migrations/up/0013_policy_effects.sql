-- 0013: policy decisions, credential broker, behavior guard, effect ledger
-- completion (SEC-002..005, EFF-001..003).
BEGIN;

CREATE TABLE policy_decisions (
    tenant_id          UUID NOT NULL,
    policy_decision_id UUID NOT NULL,
    actor_id           UUID NOT NULL,
    operation          TEXT NOT NULL,
    argument_scope_digest TEXT NOT NULL,
    target             TEXT NOT NULL,
    data_classification JSONB NOT NULL DEFAULT '[]'::jsonb,
    capability_snapshot_id UUID,
    decision           TEXT NOT NULL CHECK (decision IN ('ALLOW','ALLOW_REDACTED','REQUIRE_APPROVAL','DENY')),
    policy_revision    TEXT NOT NULL,
    expires_at         TIMESTAMPTZ NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, policy_decision_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
CREATE INDEX idx_policy_decisions_digest ON policy_decisions(tenant_id, actor_id, operation, argument_scope_digest);

-- Credential broker: secrets never leave the broker; handles are opaque.
CREATE TABLE credential_secrets (
    tenant_id     UUID NOT NULL,
    secret_id     TEXT NOT NULL,
    provider      TEXT NOT NULL,
    secret_material TEXT NOT NULL,
    generation    INT NOT NULL DEFAULT 1,
    rotated_from  TEXT,
    active        BOOLEAN NOT NULL DEFAULT true,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, secret_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE credential_handles (
    tenant_id     UUID NOT NULL,
    handle_id     UUID NOT NULL,
    secret_id     TEXT NOT NULL,
    secret_generation INT NOT NULL,
    operation     TEXT NOT NULL,
    target        TEXT NOT NULL,
    capability    TEXT NOT NULL,
    expires_at    TIMESTAMPTZ NOT NULL,
    revoked_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, handle_id),
    FOREIGN KEY (tenant_id, secret_id) REFERENCES credential_secrets(tenant_id, secret_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- Behavior-sequence guard rules and evaluation trail.
CREATE TABLE behavior_rules (
    tenant_id   UUID NOT NULL,
    rule_id     TEXT NOT NULL,
    sequence    JSONB NOT NULL,
    action      TEXT NOT NULL CHECK (action IN ('block','escalate')),
    enabled     BOOLEAN NOT NULL DEFAULT true,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, rule_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE behavior_evaluations (
    evaluation_id BIGSERIAL PRIMARY KEY,
    tenant_id   UUID NOT NULL,
    rule_id     TEXT NOT NULL,
    matched     BOOLEAN NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- Effect ledger completion: policy/approval/receipt correlation (EFF-001/002).
ALTER TABLE effects ADD COLUMN IF NOT EXISTS policy_decision_id UUID;
ALTER TABLE effects ADD COLUMN IF NOT EXISTS receipt JSONB;
ALTER TABLE effects ADD COLUMN IF NOT EXISTS idempotency_key TEXT;
ALTER TABLE effects ADD COLUMN IF NOT EXISTS state_details JSONB NOT NULL DEFAULT '{}'::jsonb;
CREATE UNIQUE INDEX idx_effects_idempotency
    ON effects(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL;

ALTER TABLE approvals ADD COLUMN IF NOT EXISTS amount_minor BIGINT;
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS ceiling_minor BIGINT;
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS currency TEXT;
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS payee TEXT;
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS argument_scope_digest TEXT NOT NULL DEFAULT '';

-- Reconciliation probes for UNKNOWN effects (EFF-003).
CREATE TABLE effect_reconciliations (
    tenant_id      UUID NOT NULL,
    effect_id      UUID NOT NULL,
    attempt        INT NOT NULL,
    probe_result   TEXT NOT NULL CHECK (probe_result IN ('committed','not_found','unknown')),
    detail         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, effect_id, attempt),
    FOREIGN KEY (tenant_id, effect_id) REFERENCES effects(tenant_id, effect_id)
);
COMMIT;
