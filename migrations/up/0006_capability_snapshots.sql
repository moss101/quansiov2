-- 0006: immutable capability snapshots (SEC-001).
-- Admission writes a frozen record; content columns are trigger-protected
-- against mutation. Only revocation may change a snapshot after admission.
BEGIN;
CREATE TABLE capability_snapshots (
    tenant_id          UUID NOT NULL,
    snapshot_id        UUID NOT NULL,
    parent_snapshot_id UUID,
    principal_id       UUID NOT NULL,
    revision           BIGINT NOT NULL,
    capabilities       JSONB NOT NULL,
    constraints        JSONB NOT NULL,
    budget_cents       BIGINT NOT NULL DEFAULT 0,
    content_digest     TEXT NOT NULL,
    admitted_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at         TIMESTAMPTZ NOT NULL,
    revoked_at         TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, snapshot_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
    FOREIGN KEY (tenant_id, parent_snapshot_id) REFERENCES capability_snapshots(tenant_id, snapshot_id)
);

CREATE OR REPLACE FUNCTION forbid_snapshot_mutation() RETURNS trigger AS $$
BEGIN
    IF NEW.capabilities::text <> OLD.capabilities::text
       OR NEW.constraints::text <> OLD.constraints::text
       OR NEW.parent_snapshot_id IS DISTINCT FROM OLD.parent_snapshot_id
       OR NEW.principal_id IS DISTINCT FROM OLD.principal_id
       OR NEW.revision IS DISTINCT FROM OLD.revision
       OR NEW.budget_cents IS DISTINCT FROM OLD.budget_cents
       OR NEW.content_digest IS DISTINCT FROM OLD.content_digest
       OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
       OR NEW.admitted_at IS DISTINCT FROM OLD.admitted_at THEN
        RAISE EXCEPTION 'capability snapshot % is immutable after admission', OLD.snapshot_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_snapshot_immutable
    BEFORE UPDATE ON capability_snapshots
    FOR EACH ROW EXECUTE FUNCTION forbid_snapshot_mutation();
COMMIT;
