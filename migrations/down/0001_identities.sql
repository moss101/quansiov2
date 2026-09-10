-- 0001 (down): remove identities and tenant authority
BEGIN;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS role_bindings;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS workspaces;
DROP TABLE IF EXISTS tenants;
COMMIT;
