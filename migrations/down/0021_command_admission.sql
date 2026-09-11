-- 0021_command_admission.sql (down)
BEGIN;
DROP INDEX IF EXISTS commands_tenant_idempotency_key;
DROP TABLE IF EXISTS commands;
COMMIT;
