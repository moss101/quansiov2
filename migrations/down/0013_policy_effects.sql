-- 0013 (down)
BEGIN;
DROP TABLE IF EXISTS effect_reconciliations;
ALTER TABLE approvals DROP COLUMN IF EXISTS argument_scope_digest;
ALTER TABLE approvals DROP COLUMN IF EXISTS payee;
ALTER TABLE approvals DROP COLUMN IF EXISTS currency;
ALTER TABLE approvals DROP COLUMN IF EXISTS ceiling_minor;
ALTER TABLE approvals DROP COLUMN IF EXISTS amount_minor;
DROP INDEX IF EXISTS idx_effects_idempotency;
ALTER TABLE effects DROP COLUMN IF EXISTS state_details;
ALTER TABLE effects DROP COLUMN IF EXISTS idempotency_key;
ALTER TABLE effects DROP COLUMN IF EXISTS receipt;
ALTER TABLE effects DROP COLUMN IF EXISTS policy_decision_id;
DROP TABLE IF EXISTS behavior_evaluations;
DROP TABLE IF EXISTS behavior_rules;
DROP TABLE IF EXISTS credential_handles;
DROP TABLE IF EXISTS credential_secrets;
DROP TABLE IF EXISTS policy_decisions;
COMMIT;
