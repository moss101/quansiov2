// Canonical contract binding for ModelRequestEnvelope.
// Generated from schemas/ModelRequestEnvelope.schema.json digest 1cdbe96e8a532e4069d359ac1fa0062c3c73c81c2fb65d73782104abb7e4869b by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const M_O_D_E_LR_E_Q_U_E_S_TE_N_V_E_L_O_P_E_SCHEMA_DIGEST = '1cdbe96e8a532e4069d359ac1fa0062c3c73c81c2fb65d73782104abb7e4869b';

export interface ModelRequestEnvelope {
  cancellation_id: string;
  capability_snapshot_id: string;
  context_projection_id: string;
  created_at: string;
  execution_generation: number;
  messages: unknown[];
  model_profile_id: string;
  privacy_decision_id?: string | undefined;
  request_id: string;
  residency_policy_id?: string | undefined;
  route_decision_id: string;
  run_id: string;
  sampling?: object | undefined;
  schema_revision: unknown;
  step_id: string;
  stream_id: string;
  tenant_id: string;
  tools?: unknown[] | undefined;
  trace_id?: string | undefined;
  usage_reservation_id: string;
  workspace_id: string;
}
