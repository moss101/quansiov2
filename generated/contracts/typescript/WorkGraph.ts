// Canonical contract binding for WorkGraph.
// Generated from schemas/WorkGraph.schema.json digest 248afe64240bee08fa3b3cc15710929543c98d3e7e2a2c130226ff6797004b90 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const W_O_R_KG_R_A_P_H_SCHEMA_DIGEST = '248afe64240bee08fa3b3cc15710929543c98d3e7e2a2c130226ff6797004b90';

export interface WorkGraph {
  edges: unknown[];
  nodes: unknown[];
  revision: number;
  run_id: string;
  schema_revision: unknown;
  state: unknown;
  tenant_id: string;
  workgraph_id: string;
  workspace_id: string;
}
