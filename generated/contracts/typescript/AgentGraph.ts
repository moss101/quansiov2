// Canonical contract binding for AgentGraph.
// Generated from schemas/AgentGraph.schema.json digest 04b1a5611a5d334842f21b95cb6cfb3dc5dd99ce31f194da3d2373b15724d1ee by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const A_G_E_N_TG_R_A_P_H_SCHEMA_DIGEST = '04b1a5611a5d334842f21b95cb6cfb3dc5dd99ce31f194da3d2373b15724d1ee';

export interface AgentGraph {
  agentgraph_id: string;
  agents: unknown[];
  schema_revision: unknown;
  tenant_id: string;
  workspace_id: string;
}
