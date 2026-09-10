-- 0011: model gateway durable state (MOD-001..MOD-007).
BEGIN;
CREATE TABLE model_requests (
    tenant_id        UUID NOT NULL,
    request_id       UUID NOT NULL,
    run_id           UUID NOT NULL,
    step_id          TEXT NOT NULL,
    model_profile_id TEXT NOT NULL,
    route_decision_id UUID NOT NULL,
    usage_reservation_id UUID,
    state            TEXT NOT NULL CHECK (state IN ('admitted','streaming','completed','cancelled','failed','interrupted')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, request_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE model_events (
    tenant_id    UUID NOT NULL,
    request_id   UUID NOT NULL,
    sequence     BIGINT NOT NULL,
    event_id     UUID NOT NULL,
    event_type   TEXT NOT NULL,
    payload      JSONB NOT NULL,
    delivered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, request_id, sequence),
    FOREIGN KEY (tenant_id, request_id) REFERENCES model_requests(tenant_id, request_id)
);

CREATE TABLE model_privacy_decisions (
    tenant_id          UUID NOT NULL,
    privacy_decision_id UUID NOT NULL,
    request_id         UUID NOT NULL,
    destination_profile TEXT NOT NULL,
    decision           TEXT NOT NULL CHECK (decision IN ('ALLOW','ALLOW_REDACTED','DENY')),
    classifications    JSONB NOT NULL DEFAULT '[]'::jsonb,
    redactions         INT NOT NULL DEFAULT 0,
    policy_revision    TEXT NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, privacy_decision_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE route_decisions (
    tenant_id         UUID NOT NULL,
    route_decision_id UUID NOT NULL,
    algorithm_version TEXT NOT NULL,
    catalog_version   TEXT NOT NULL,
    selected_profile_id TEXT NOT NULL,
    ranked_profile_ids JSONB NOT NULL,
    inputs_digest     TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, route_decision_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE model_usage_settlements (
    settlement_id  BIGSERIAL PRIMARY KEY,
    tenant_id      UUID NOT NULL,
    request_id     UUID NOT NULL,
    reservation_id UUID NOT NULL,
    kind           TEXT NOT NULL CHECK (kind IN ('final','streamed','policy_adjustment','release')),
    tokens         BIGINT NOT NULL DEFAULT 0,
    cents          BIGINT NOT NULL DEFAULT 0,
    payload        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE provider_health (
    tenant_id  UUID NOT NULL,
    profile_id TEXT NOT NULL,
    state      TEXT NOT NULL CHECK (state IN ('healthy','suspect','down')),
    reason     TEXT NOT NULL,
    probed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, profile_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE provider_failures (
    failure_id BIGSERIAL PRIMARY KEY,
    tenant_id  UUID NOT NULL,
    profile_id TEXT NOT NULL,
    kind       TEXT NOT NULL,
    detail     TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
COMMIT;
