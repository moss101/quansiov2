-- 0010 (down)
BEGIN;
DROP TRIGGER IF EXISTS trg_effects_committed_guard ON effects;
DROP FUNCTION IF EXISTS forbid_cancellation_rollback();
COMMIT;
