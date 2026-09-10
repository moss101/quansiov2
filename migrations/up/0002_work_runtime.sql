-- 0002: work, runtime, protocol, approval, effect, schedule and registry state.
-- All application aggregates are tenant-scoped with composite foreign keys.
BEGIN;

-- Persistent teammate / agent identities (RUN-002 depends on this shape).
CREATE TABLE agents (
    tenant_id     UUID NOT NULL REFERENCES tenants(tenant_id),
    workspace_id  UUID NOT NULL,
    agent_id      UUID NOT NULL,
    kind          TEXT NOT NULL CHECK (kind IN ('persistent_teammate', 'ephemeral_worker')),
    display_name  TEXT NOT NULL,
    parent_agent_id UUID,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    retired_at    TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, agent_id),
    FOREIGN KEY (tenant_id, workspace_id) REFERENCES workspaces(tenant_id, workspace_id),
    FOREIGN KEY (tenant_id, parent_agent_id) REFERENCES agents(tenant_id, agent_id),
    UNIQUE (tenant_id, workspace_id, display_name)
);

-- Runs: one execution of a graph by an agent.
CREATE TABLE runs (
    tenant_id     UUID NOT NULL REFERENCES tenants(tenant_id),
    workspace_id  UUID NOT NULL,
    run_id        UUID NOT NULL,
    agent_id      UUID NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('pending','running','suspended','succeeded','failed','cancelled')),
    generation    BIGINT NOT NULL DEFAULT 0,
    budget_cents  BIGINT NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    terminal_at   TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, run_id),
    FOREIGN KEY (tenant_id, workspace_id) REFERENCES workspaces(tenant_id, workspace_id),
    FOREIGN KEY (tenant_id, agent_id) REFERENCES agents(tenant_id, agent_id)
);

-- Canonical graphs (WorkGraph/AgentGraph/StateGraph share one persistence shape).
CREATE TABLE graphs (
    tenant_id     UUID NOT NULL REFERENCES tenants(tenant_id),
    workspace_id  UUID NOT NULL,
    graph_id      UUID NOT NULL,
    run_id        UUID,
    graph_kind    TEXT NOT NULL CHECK (graph_kind IN ('work','agent','state')),
    revision      BIGINT NOT NULL DEFAULT 0,
    spec          JSONB NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, graph_id),
    FOREIGN KEY (tenant_id, workspace_id) REFERENCES workspaces(tenant_id, workspace_id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES runs(tenant_id, run_id)
);

CREATE TABLE graph_nodes (
    tenant_id   UUID NOT NULL,
    graph_id    UUID NOT NULL,
    node_id     TEXT NOT NULL,
    node_kind   TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('pending','ready','running','succeeded','failed','skipped','cancelled')),
    deadline_at TIMESTAMPTZ,
    payload     JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (tenant_id, graph_id, node_id),
    FOREIGN KEY (tenant_id, graph_id) REFERENCES graphs(tenant_id, graph_id) ON DELETE CASCADE
);

-- Durable wait/protocol state, separate from semantic memory (DAT-005).
CREATE TABLE protocol_state (
    tenant_id    UUID NOT NULL,
    workspace_id UUID NOT NULL,
    state_id     UUID NOT NULL,
    run_id       UUID,
    state_kind   TEXT NOT NULL CHECK (state_kind IN ('tool_call','approval_wait','question','worker_lifecycle','browser_ownership','cancellation','durable_wait','timer_wait','callback_wait')),
    status       TEXT NOT NULL,
    payload      JSONB NOT NULL DEFAULT '{}'::jsonb,
    resume_at    TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, state_id),
    FOREIGN KEY (tenant_id, workspace_id) REFERENCES workspaces(tenant_id, workspace_id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES runs(tenant_id, run_id)
);
CREATE INDEX idx_protocol_state_resume ON protocol_state(resume_at) WHERE status IN ('waiting','open');

-- Approvals (durable, scoped; EFF-002 owns semantics).
CREATE TABLE approvals (
    tenant_id    UUID NOT NULL,
    workspace_id UUID NOT NULL,
    approval_id  UUID NOT NULL,
    run_id       UUID,
    capability   TEXT NOT NULL,
    arguments    JSONB NOT NULL,
    scope        JSONB NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('pending','approved','denied','expired','superseded')),
    decided_by   UUID,
    decided_at   TIMESTAMPTZ,
    expires_at   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, approval_id),
    FOREIGN KEY (tenant_id, workspace_id) REFERENCES workspaces(tenant_id, workspace_id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES runs(tenant_id, run_id)
);

-- Effect ledger (one effect path; EFF-001 owns semantics).
CREATE TABLE effects (
    tenant_id    UUID NOT NULL,
    workspace_id UUID NOT NULL,
    effect_id    UUID NOT NULL,
    run_id       UUID,
    approval_id  UUID,
    operation    TEXT NOT NULL,
    arguments    JSONB NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('proposed','authorized','actuating','committed','failed','unknown','reconciled','rolled_back')),
    result       JSONB,
    attempt      INT NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, effect_id),
    FOREIGN KEY (tenant_id, workspace_id) REFERENCES workspaces(tenant_id, workspace_id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES runs(tenant_id, run_id),
    FOREIGN KEY (tenant_id, approval_id) REFERENCES approvals(tenant_id, approval_id)
);

-- Automation schedules (AUT-001 owns semantics).
CREATE TABLE schedules (
    tenant_id    UUID NOT NULL,
    workspace_id UUID NOT NULL,
    schedule_id  UUID NOT NULL,
    name         TEXT NOT NULL,
    cron         TEXT NOT NULL,
    timezone     TEXT NOT NULL,
    payload      JSONB NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('active','paused','deleted')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, schedule_id),
    FOREIGN KEY (tenant_id, workspace_id) REFERENCES workspaces(tenant_id, workspace_id)
);

-- Registries: canonical tool/registry configuration authority.
CREATE TABLE registry_entries (
    tenant_id    UUID NOT NULL,
    registry     TEXT NOT NULL CHECK (registry IN ('tool','capability','model_profile','support','connector')),
    entry_id     TEXT NOT NULL,
    revision     BIGINT NOT NULL DEFAULT 1,
    definition   JSONB NOT NULL,
    enabled      BOOLEAN NOT NULL DEFAULT true,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, registry, entry_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
COMMIT;
