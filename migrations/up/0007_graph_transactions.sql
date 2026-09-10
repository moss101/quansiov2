-- 0007: graph transaction guard and transition identity (RUN-001/RUN-003).
-- Node/graph state may only be mutated inside a GraphTransaction, which sets
-- the `app.mutation_context` GUC for its database transaction. Direct
-- updates are rejected by triggers. Transition identity makes re-applying a
-- committed transition a no-op during recovery.
BEGIN;
ALTER TABLE graph_nodes ADD COLUMN IF NOT EXISTS transition_id UUID;
ALTER TABLE graphs ADD COLUMN IF NOT EXISTS last_transition_id UUID;

CREATE OR REPLACE FUNCTION forbid_direct_graph_mutation() RETURNS trigger AS $$
BEGIN
    IF COALESCE(current_setting('app.mutation_context', true), '') <> 'graph_transaction' THEN
        RAISE EXCEPTION 'direct mutation of % is forbidden; use GraphTransaction', TG_TABLE_NAME;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_graph_nodes_guarded ON graph_nodes;
CREATE TRIGGER trg_graph_nodes_guarded
    BEFORE UPDATE OF status, payload, transition_id ON graph_nodes
    FOR EACH ROW EXECUTE FUNCTION forbid_direct_graph_mutation();

DROP TRIGGER IF EXISTS trg_graphs_guarded ON graphs;
CREATE TRIGGER trg_graphs_guarded
    BEFORE UPDATE OF revision, spec, last_transition_id ON graphs
    FOR EACH ROW EXECUTE FUNCTION forbid_direct_graph_mutation();

-- Idempotent transition ledger: a committed transition id can never be
-- applied twice.
CREATE TABLE graph_transitions (
    tenant_id      UUID NOT NULL,
    graph_id       UUID NOT NULL,
    transition_id  UUID NOT NULL,
    applied_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, graph_id, transition_id),
    FOREIGN KEY (tenant_id, graph_id) REFERENCES graphs(tenant_id, graph_id)
);
COMMIT;
