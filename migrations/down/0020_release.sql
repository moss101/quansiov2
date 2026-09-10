-- 0020 (down)
BEGIN;
DROP TABLE IF EXISTS readiness_bundles;
DROP TABLE IF EXISTS release_events;
DROP TABLE IF EXISTS release_suite_runs;
DROP TABLE IF EXISTS release_candidates;
COMMIT;
