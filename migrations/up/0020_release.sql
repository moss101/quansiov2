-- 0020: release state machine (REL-001..008, GATE-M14 sole owner).
BEGIN;
CREATE TABLE release_candidates (
    tenant_id     UUID NOT NULL,
    candidate_id  TEXT NOT NULL,
    commit_sha    TEXT NOT NULL,
    bindings_digest  TEXT NOT NULL,
    migrations    TEXT[] NOT NULL DEFAULT '{}',
    support_selection JSONB NOT NULL,
    candidate_digest TEXT NOT NULL,
    state         TEXT NOT NULL CHECK (state IN ('created','materialized','qualified','canary_deployed','rollback_proven','go_approved','readiness_sealed','production_ready')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, candidate_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE release_suite_runs (
    suite_run_id BIGSERIAL PRIMARY KEY,
    tenant_id    UUID NOT NULL,
    candidate_id TEXT NOT NULL,
    suite_id     TEXT NOT NULL,
    passed       BOOLEAN NOT NULL,
    report_digest TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, candidate_id) REFERENCES release_candidates(tenant_id, candidate_id)
);

CREATE TABLE release_events (
    event_id   BIGSERIAL PRIMARY KEY,
    tenant_id  UUID NOT NULL,
    candidate_id TEXT NOT NULL,
    kind       TEXT NOT NULL,
    actor      TEXT NOT NULL,
    detail     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, candidate_id) REFERENCES release_candidates(tenant_id, candidate_id)
);

CREATE TABLE readiness_bundles (
    tenant_id     UUID NOT NULL,
    bundle_digest TEXT NOT NULL,
    candidate_id  TEXT NOT NULL,
    contents      JSONB NOT NULL,
    sealed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, bundle_digest),
    FOREIGN KEY (tenant_id, candidate_id) REFERENCES release_candidates(tenant_id, candidate_id)
);
COMMIT;
