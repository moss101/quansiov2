// Canonical contract binding for StateGraph.
// Generated from schemas/StateGraph.schema.json digest f133256fb067831e6d093e80d4dd5f0e4f3683ce5a6399860da5a00a109c7e40 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const S_T_A_T_EG_R_A_P_H_SCHEMA_DIGEST = 'f133256fb067831e6d093e80d4dd5f0e4f3683ce5a6399860da5a00a109c7e40';

export interface StateGraph {
  revision: number;
  run_id: string;
  schema_revision: unknown;
  stategraph_id: string;
  states: object;
  tenant_id: string;
}
