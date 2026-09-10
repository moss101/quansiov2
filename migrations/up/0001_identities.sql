-- 0001: identities and tenant authority (quansio-control owned)
-- Every tenant-scoped reference is a composite (tenant_id, <entity>_id)
-- foreign key so a cross-tenant reference cannot exist at the storage level.
BEGIN;

CREATE TABLE tenants (
    tenant_id    UUID PRIMARY KEY,
    name         TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE workspaces (
    tenant_id    UUID NOT NULL REFERENCES tenants(tenant_id),
    workspace_id UUID NOT NULL,
    name         TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, workspace_id),
    UNIQUE (tenant_id, name)
);

CREATE TABLE users (
    tenant_id     UUID NOT NULL REFERENCES tenants(tenant_id),
    user_id       UUID NOT NULL,
    email         TEXT NOT NULL,
    display_name  TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, user_id),
    UNIQUE (tenant_id, email)
);

CREATE TABLE role_bindings (
    binding_id   UUID PRIMARY KEY,
    tenant_id  UUID NOT NULL REFERENCES tenants(tenant_id),
    user_id    UUID NOT NULL,
    workspace_id UUID,
    role       TEXT NOT NULL CHECK (role IN ('tenant_admin', 'workspace_admin', 'member', 'observer')),
    granted_by UUID,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, user_id) REFERENCES users(tenant_id, user_id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, workspace_id) REFERENCES workspaces(tenant_id, workspace_id)
);
CREATE UNIQUE INDEX idx_role_bindings_unique
    ON role_bindings(tenant_id, user_id, role, workspace_id);
CREATE INDEX idx_role_bindings_tenant_wide
    ON role_bindings(tenant_id, user_id, role) WHERE workspace_id IS NULL;

CREATE TABLE sessions (
    session_id   UUID PRIMARY KEY,
    tenant_id    UUID NOT NULL REFERENCES tenants(tenant_id),
    user_id      UUID NOT NULL,
    workspace_id UUID NOT NULL,
    token_hash   TEXT NOT NULL UNIQUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at   TIMESTAMPTZ NOT NULL,
    revoked_at   TIMESTAMPTZ,
    FOREIGN KEY (tenant_id, user_id) REFERENCES users(tenant_id, user_id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, workspace_id) REFERENCES workspaces(tenant_id, workspace_id)
);

CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_sessions_expiry ON sessions(expires_at) WHERE revoked_at IS NULL;
COMMIT;
