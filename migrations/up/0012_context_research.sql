-- 0012: context/research durable state (CTX-001..CTX-008).
BEGIN;

-- Durable operator outputs for SearchProgram resume (CTX-001/004).
CREATE TABLE program_runs (
    tenant_id    UUID NOT NULL,
    program_id   UUID NOT NULL,
    spec_digest  TEXT NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('running','completed','failed','cancelled')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, program_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE program_step_outputs (
    tenant_id     UUID NOT NULL,
    program_id    UUID NOT NULL,
    step_index    INT NOT NULL,
    input_digest  TEXT NOT NULL,
    output        JSONB NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('complete','partial','budget_exceeded','timed_out','failed')),
    operator      TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, program_id, step_index, input_digest),
    FOREIGN KEY (tenant_id, program_id) REFERENCES program_runs(tenant_id, program_id)
);

-- Research entities: canonical identity with versioned evidence (CTX-003).
CREATE TABLE research_entities (
    tenant_id      UUID NOT NULL,
    program_id     UUID NOT NULL,
    entity_key     TEXT NOT NULL,
    entity_version INT NOT NULL DEFAULT 1,
    display_name   TEXT NOT NULL,
    attributes     JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence     REAL NOT NULL DEFAULT 0,
    verification   TEXT NOT NULL DEFAULT 'unverified',
    superseded_by  TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, program_id, entity_key, entity_version),
    FOREIGN KEY (tenant_id, program_id) REFERENCES program_runs(tenant_id, program_id)
);

CREATE TABLE research_entity_evidence (
    evidence_id  BIGSERIAL PRIMARY KEY,
    tenant_id    UUID NOT NULL,
    program_id   UUID NOT NULL,
    entity_key   TEXT NOT NULL,
    entity_version INT NOT NULL,
    kind         TEXT NOT NULL CHECK (kind IN ('supporting','identity_correction','superseded_identity')),
    source_digest TEXT NOT NULL,
    detail       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, program_id) REFERENCES program_runs(tenant_id, program_id)
);

CREATE TABLE research_claims (
    claim_id    UUID NOT NULL,
    tenant_id   UUID NOT NULL,
    program_id  UUID NOT NULL,
    entity_key  TEXT NOT NULL,
    claim_digest TEXT NOT NULL,
    statement   TEXT NOT NULL,
    source_digests TEXT[] NOT NULL DEFAULT '{}',
    verification TEXT NOT NULL DEFAULT 'unverified'
        CHECK (verification IN ('unverified','supported','unsupported','stale','inaccessible','conflicting')),
    evidence_detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, claim_id),
    FOREIGN KEY (tenant_id, program_id) REFERENCES program_runs(tenant_id, program_id)
);

-- Indexer: sources, chunks, tombstones, freshness watermark (CTX-007).
CREATE TABLE index_sources (
    tenant_id     UUID NOT NULL,
    source_id     TEXT NOT NULL,
    revision      INT NOT NULL DEFAULT 1,
    url           TEXT NOT NULL,
    state         TEXT NOT NULL CHECK (state IN ('active','tombstoned','deleted')),
    freshness_watermark TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant_id, source_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE indexed_chunks (
    tenant_id   UUID NOT NULL,
    source_id   TEXT NOT NULL,
    chunk_id    TEXT NOT NULL,
    revision    INT NOT NULL,
    content     TEXT NOT NULL,
    content_digest TEXT NOT NULL,
    provenance  JSONB NOT NULL DEFAULT '{}'::jsonb,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, source_id, chunk_id),
    FOREIGN KEY (tenant_id, source_id) REFERENCES index_sources(tenant_id, source_id)
);
CREATE INDEX idx_chunks_source_rev ON indexed_chunks(tenant_id, source_id, revision);

CREATE TABLE context_projections (
    tenant_id      UUID NOT NULL,
    projection_id  UUID NOT NULL,
    run_id         UUID NOT NULL,
    step_id        TEXT NOT NULL,
    source_epoch   TEXT NOT NULL,
    projection_digest TEXT NOT NULL,
    token_budget   INT NOT NULL,
    tokens_used    INT NOT NULL,
    content        JSONB NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, projection_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE benchmark_results (
    tenant_id        UUID NOT NULL,
    benchmark_id     TEXT NOT NULL,
    dataset_digest   TEXT NOT NULL,
    scorer_version   TEXT NOT NULL,
    source_policy    TEXT NOT NULL,
    metrics          JSONB NOT NULL,
    outputs_digest   TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, benchmark_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
COMMIT;
