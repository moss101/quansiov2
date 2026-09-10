-- 0012 (down)
BEGIN;
DROP TABLE IF EXISTS benchmark_results;
DROP TABLE IF EXISTS context_projections;
DROP TABLE IF EXISTS indexed_chunks;
DROP TABLE IF EXISTS index_sources;
DROP TABLE IF EXISTS research_claims;
DROP TABLE IF EXISTS research_entity_evidence;
DROP TABLE IF EXISTS research_entities;
DROP TABLE IF EXISTS program_step_outputs;
DROP TABLE IF EXISTS program_runs;
COMMIT;
