-- 0018: automation scheduling + collaboration (AUT-001..004, COL-001..004).
BEGIN;
CREATE TABLE automations (
    tenant_id      UUID NOT NULL,
    automation_id  UUID NOT NULL,
    name           TEXT NOT NULL,
    timezone       TEXT NOT NULL,
    cron           TEXT NOT NULL,
    fold_gap_policy TEXT NOT NULL CHECK (fold_gap_policy IN ('earliest','latest','skip')),
    catchup_policy TEXT NOT NULL CHECK (catchup_policy IN ('SKIP','FIRE_ONCE','CATCH_UP_BOUNDED')),
    catchup_max    INT NOT NULL DEFAULT 0,
    lifecycle      TEXT NOT NULL CHECK (lifecycle IN ('active','paused','deleted')),
    work_template  JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, automation_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE automation_occurrences (
    tenant_id      UUID NOT NULL,
    automation_id  UUID NOT NULL,
    logical_fire   TEXT NOT NULL,
    fire_time_utc  TIMESTAMPTZ NOT NULL,
    state          TEXT NOT NULL CHECK (state IN ('pending','fired','skipped','catchup_skipped','blocked_attention')),
    blocked_reason TEXT,
    PRIMARY KEY (tenant_id, automation_id, logical_fire),
    FOREIGN KEY (tenant_id, automation_id) REFERENCES automations(tenant_id, automation_id)
);

CREATE TABLE collaborator_rooms (
    tenant_id    UUID NOT NULL,
    room_id      UUID NOT NULL,
    name         TEXT NOT NULL,
    workspace_id UUID NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, room_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE room_participants (
    participant_id BIGSERIAL PRIMARY KEY,
    tenant_id    UUID NOT NULL,
    room_id      UUID NOT NULL,
    agent_id     UUID NOT NULL,
    role         TEXT NOT NULL,
    joined_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, room_id) REFERENCES collaborator_rooms(tenant_id, room_id)
);

CREATE TABLE room_messages (
    message_id  UUID NOT NULL,
    tenant_id   UUID NOT NULL,
    room_id     UUID NOT NULL,
    turn_id     UUID,
    sender_agent UUID NOT NULL,
    payload     JSONB NOT NULL,
    artifact_refs TEXT[] NOT NULL DEFAULT '{}',
    capability_context TEXT NOT NULL,
    delivery_state TEXT NOT NULL CHECK (delivery_state IN ('pending','delivered','failed','cancelled')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, message_id),
    FOREIGN KEY (tenant_id, room_id) REFERENCES collaborator_rooms(tenant_id, room_id)
);

CREATE TABLE notifications (
    notification_id UUID NOT NULL,
    tenant_id    UUID NOT NULL,
    recipient_id UUID NOT NULL,
    channel_class TEXT NOT NULL,
    urgency      TEXT NOT NULL CHECK (urgency IN ('low','normal','high','critical')),
    expires_at   TIMESTAMPTZ NOT NULL,
    deep_link    TEXT NOT NULL,
    payload      JSONB NOT NULL,
    state        TEXT NOT NULL CHECK (state IN ('pending','delivered','acknowledged','expired')),
    delivered_at TIMESTAMPTZ,
    acknowledged_by UUID,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, notification_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
COMMIT;
