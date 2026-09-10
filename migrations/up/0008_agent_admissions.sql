-- 0008: ephemeral worker admission expiry (RUN-002).
BEGIN;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS admission_expires_at TIMESTAMPTZ;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS admission_snapshot_id UUID;
CREATE INDEX idx_agents_ephemeral_expiry ON agents(admission_expires_at)
    WHERE kind = 'ephemeral_worker' AND retired_at IS NULL;
COMMIT;
