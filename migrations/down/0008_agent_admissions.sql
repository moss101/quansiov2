-- 0008 (down)
BEGIN;
DROP INDEX IF EXISTS idx_agents_ephemeral_expiry;
ALTER TABLE agents DROP COLUMN IF EXISTS admission_snapshot_id;
ALTER TABLE agents DROP COLUMN IF EXISTS admission_expires_at;
COMMIT;
