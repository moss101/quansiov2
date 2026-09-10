-- 0010: committed external effects are immutable to cancellation (RUN-006).
-- Only the effect reconciliation flow (app.effect_reconciliation = 'true')
-- may move a committed effect to rolled_back.
BEGIN;
CREATE OR REPLACE FUNCTION forbid_cancellation_rollback() RETURNS trigger AS $$
BEGIN
    IF OLD.status = 'committed' AND NEW.status = 'rolled_back'
       AND COALESCE(current_setting('app.effect_reconciliation', true), '') <> 'true' THEN
        RAISE EXCEPTION 'committed external effect % cannot be rolled back by cancellation alone', OLD.effect_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_effects_committed_guard ON effects;
CREATE TRIGGER trg_effects_committed_guard
    BEFORE UPDATE OF status ON effects
    FOR EACH ROW EXECUTE FUNCTION forbid_cancellation_rollback();
COMMIT;
