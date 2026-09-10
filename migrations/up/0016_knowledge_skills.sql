-- 0016: knowledge fabric + skill lifecycle (KNW-001..003, SKL-001..005).
BEGIN;
CREATE TABLE knowledge_candidates (
    tenant_id      UUID NOT NULL,
    candidate_id   UUID NOT NULL,
    fabric_kind    TEXT NOT NULL CHECK (fabric_kind IN ('enterprise','user','research','work','engineering')),
    content        JSONB NOT NULL,
    provenance     JSONB NOT NULL,
    evidence_refs  TEXT[] NOT NULL DEFAULT '{}',
    source_epoch   TEXT NOT NULL,
    task_epoch     TEXT,
    confidence     REAL NOT NULL DEFAULT 0,
    valid_from     TIMESTAMPTZ,
    valid_until    TIMESTAMPTZ,
    conflict_set   TEXT[] NOT NULL DEFAULT '{}',
    producer       TEXT NOT NULL,
    run_id         UUID,
    status         TEXT NOT NULL CHECK (status IN ('candidate','accepted','rejected','stale','withdrawn')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, candidate_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE skill_packages (
    tenant_id       UUID NOT NULL,
    skill_name      TEXT NOT NULL,
    version         INT NOT NULL,
    purpose         TEXT NOT NULL,
    inputs_schema   JSONB NOT NULL,
    outputs_schema  JSONB NOT NULL,
    instructions    TEXT NOT NULL,
    dependencies    JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_scope    JSONB NOT NULL,
    intended_use    TEXT NOT NULL,
    exclusions      TEXT NOT NULL,
    source_material_digest TEXT NOT NULL,
    state           TEXT NOT NULL CHECK (state IN ('candidate','evaluated','qualified','promoted','rolled_back','blocked')),
    evaluation_digest TEXT,
    regression_report JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, skill_name, version),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE skill_evaluations (
    evaluation_id BIGSERIAL PRIMARY KEY,
    tenant_id     UUID NOT NULL,
    skill_name    TEXT NOT NULL,
    version       INT NOT NULL,
    evaluator_version TEXT NOT NULL,
    findings      JSONB NOT NULL,
    passed        BOOLEAN NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE skill_registrations (
    tenant_id    UUID NOT NULL,
    skill_name   TEXT NOT NULL,
    active_version INT NOT NULL,
    rollback_target INT,
    compatibility TEXT NOT NULL DEFAULT '{}',
    thresholds   JSONB NOT NULL DEFAULT '{}'::jsonb,
    promoted_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, skill_name),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE skill_materializations (
    materialization_id UUID NOT NULL,
    tenant_id    UUID NOT NULL,
    task_id      TEXT NOT NULL,
    skill_name   TEXT NOT NULL,
    version      INT NOT NULL,
    state        TEXT NOT NULL CHECK (state IN ('materialized','removed')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, materialization_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
COMMIT;
