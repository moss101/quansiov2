-- 0019: SRE/security qualification state (SRE-001..006, SEC-006..007).
BEGIN;
CREATE TABLE telemetry_spans (
    span_id     UUID NOT NULL,
    tenant_id   UUID NOT NULL,
    trace_id    UUID NOT NULL,
    parent_span UUID,
    boundary    TEXT NOT NULL,
    operation   TEXT NOT NULL,
    correlation JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    duration_ms INT,
    status      TEXT NOT NULL DEFAULT 'ok',
    PRIMARY KEY (tenant_id, span_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE slo_observations (
    observation_id BIGSERIAL PRIMARY KEY,
    tenant_id    UUID NOT NULL,
    sli_name     TEXT NOT NULL,
    ok           BOOLEAN NOT NULL,
    latency_ms   INT,
    observed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    excluded     BOOLEAN NOT NULL DEFAULT false,
    exclusion_rule TEXT
);

CREATE TABLE recovery_points (
    tenant_id      UUID NOT NULL,
    rcp_id         UUID NOT NULL,
    db_commit_position TEXT NOT NULL,
    event_sequence BIGINT NOT NULL,
    evidence_manifest_digest TEXT NOT NULL,
    snapshot_inventory_digest TEXT NOT NULL,
    effect_settlement_watermark BIGINT NOT NULL,
    unknown_effect_ids UUID[] NOT NULL DEFAULT '{}',
    state          TEXT NOT NULL CHECK (state IN ('open','verified','restored')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, rcp_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE dr_drills (
    drill_id    UUID NOT NULL,
    tenant_id   UUID NOT NULL,
    rcp_id      UUID NOT NULL,
    objective   TEXT NOT NULL CHECK (objective IN ('authoritative','evidence')),
    rpo_seconds INT NOT NULL,
    rto_seconds INT NOT NULL,
    passed      BOOLEAN NOT NULL,
    detail      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (drill_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE tenant_quotas (
    tenant_id  UUID NOT NULL,
    kind       TEXT NOT NULL CHECK (kind IN ('model_cents','research_fanout','workers','storage_bytes','connector_calls')),
    limit_value BIGINT NOT NULL,
    PRIMARY KEY (tenant_id, kind),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE tenant_quota_spend (
    tenant_id  UUID NOT NULL,
    kind       TEXT NOT NULL,
    spent      BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, kind),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE adversarial_probes (
    probe_id   BIGSERIAL PRIMARY KEY,
    tenant_id  UUID NOT NULL,
    probe_kind TEXT NOT NULL,
    denied     BOOLEAN NOT NULL,
    detail     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE provenance_manifests (
    manifest_id UUID NOT NULL,
    tenant_id   UUID NOT NULL,
    commit      TEXT NOT NULL,
    inputs      JSONB NOT NULL,
    inputs_digest TEXT NOT NULL,
    reproducible BOOLEAN NOT NULL DEFAULT true,
    nondeterministic_exclusions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, manifest_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
COMMIT;
