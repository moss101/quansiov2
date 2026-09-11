-- 0021_command_admission.sql
-- Durable command admission (quansio-runtime authority): every admitted
-- public command is persisted before any run is created, and the run it
-- produced is linked so the command-to-result journey is auditable and
-- idempotent by (tenant, idempotency_key).
BEGIN;

CREATE TABLE commands (
    tenant_id       UUID NOT NULL REFERENCES tenants(tenant_id),
    command_id      UUID NOT NULL,
    workspace_id    UUID NOT NULL,
    actor_id        UUID NOT NULL,
    session_id      UUID NOT NULL,
    command_type    TEXT NOT NULL,
    arguments       JSONB NOT NULL,
    idempotency_key TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('admitted', 'dispatched')),
    run_id          UUID,
    admitted_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    dispatched_at   TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, command_id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES runs(tenant_id, run_id)
);

CREATE UNIQUE INDEX commands_tenant_idempotency_key
    ON commands (tenant_id, idempotency_key);

COMMIT;
