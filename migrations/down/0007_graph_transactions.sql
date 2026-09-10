-- 0007 (down)
BEGIN;
DROP TABLE IF EXISTS graph_transitions;
DROP TRIGGER IF EXISTS trg_graphs_guarded ON graphs;
DROP TRIGGER IF EXISTS trg_graph_nodes_guarded ON graph_nodes;
DROP FUNCTION IF EXISTS forbid_direct_graph_mutation();
ALTER TABLE graphs DROP COLUMN IF EXISTS last_transition_id;
ALTER TABLE graph_nodes DROP COLUMN IF EXISTS transition_id;
COMMIT;
