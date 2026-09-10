-- 0014 (down)
BEGIN;
DROP TABLE IF EXISTS checkpoints;
DROP TABLE IF EXISTS workspace_computers;
DROP TABLE IF EXISTS task_environments;
DROP TABLE IF EXISTS worker_results;
DROP TABLE IF EXISTS worker_deliveries;
DROP TABLE IF EXISTS target_leases;
DROP TABLE IF EXISTS fence_counters;
DROP TABLE IF EXISTS target_events;
DROP TABLE IF EXISTS execution_targets;
COMMIT;
