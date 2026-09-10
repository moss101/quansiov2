-- 0011 (down)
BEGIN;
DROP TABLE IF EXISTS provider_failures;
DROP TABLE IF EXISTS provider_health;
DROP TABLE IF EXISTS model_usage_settlements;
DROP TABLE IF EXISTS route_decisions;
DROP TABLE IF EXISTS model_privacy_decisions;
DROP TABLE IF EXISTS model_events;
DROP TABLE IF EXISTS model_requests;
COMMIT;
