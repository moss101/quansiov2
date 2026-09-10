// Canonical contract binding for ModelEvent.
// Generated from schemas/ModelEvent.schema.json digest 064735a61877a86f0a271d3a19a902edd90647ef4cc189364d600e2bbc834b39 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const M_O_D_E_LE_V_E_N_T_SCHEMA_DIGEST = '064735a61877a86f0a271d3a19a902edd90647ef4cc189364d600e2bbc834b39';

export interface ModelEvent {
  event_id: string;
  event_type: unknown;
  execution_generation: number;
  model_profile_id: string;
  occurred_at: string;
  payload: object;
  request_id: string;
  route_decision_id: string;
  run_id: string;
  schema_revision: unknown;
  sequence: number;
  step_id: string;
}
