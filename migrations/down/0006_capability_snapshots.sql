-- 0006 (down)
BEGIN;
DROP TABLE IF EXISTS capability_snapshots;
DROP FUNCTION IF EXISTS forbid_snapshot_mutation();
COMMIT;
