// Canonical contract binding for EndpointActionEnvelope.
// Generated from schemas/EndpointActionEnvelope.schema.json digest 5f4e91a66b6301bc5f6dd3691846fd4238d06e4b00a88996be503f8e2b63868e by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const E_N_D_P_O_I_N_TA_C_T_I_O_NE_N_V_E_L_O_P_E_SCHEMA_DIGEST = '5f4e91a66b6301bc5f6dd3691846fd4238d06e4b00a88996be503f8e2b63868e';

export interface EndpointActionEnvelope {
  action_id: string;
  approval_receipt_id?: string | unknown | undefined;
  approval_required: boolean;
  approval_scope_digest?: string | unknown | undefined;
  arguments: object;
  capability_snapshot_id: string;
  delivery_attempt: number;
  delivery_id: string;
  effect_class: unknown;
  effect_id: string;
  endpoint_id: string;
  execution_generation: number;
  expires_at: string;
  fence_token: number;
  idempotency_key: string;
  input_schema_id: string;
  lease_id: string;
  operation_id: string;
  operation_version: string;
  policy_decision_id: string;
  schema_revision: unknown;
  target_id: string;
  tenant_id: string;
}
