-- 0019 (down)
BEGIN;
DROP TABLE IF EXISTS provenance_manifests;
DROP TABLE IF EXISTS adversarial_probes;
DROP TABLE IF EXISTS tenant_quota_spend;
DROP TABLE IF EXISTS tenant_quotas;
DROP TABLE IF EXISTS dr_drills;
DROP TABLE IF EXISTS recovery_points;
DROP TABLE IF EXISTS slo_observations;
DROP TABLE IF EXISTS telemetry_spans;
COMMIT;
