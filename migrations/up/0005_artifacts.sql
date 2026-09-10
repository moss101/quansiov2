-- 0005: artifact metadata for immutable digest-addressed storage.
BEGIN;
CREATE TABLE artifact_records (
    tenant_id    UUID NOT NULL,
    digest       TEXT NOT NULL CHECK (digest ~ '^[a-f0-9]{64}$'),
    media_type   TEXT NOT NULL,
    producer     UUID,
    size_bytes   BIGINT NOT NULL CHECK (size_bytes >= 0),
    scan_state   TEXT NOT NULL CHECK (scan_state IN ('unscanned', 'verified', 'quarantined')),
    grants       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, digest),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
COMMIT;
