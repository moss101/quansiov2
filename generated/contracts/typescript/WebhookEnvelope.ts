// Canonical contract binding for WebhookEnvelope.
// Generated from schemas/WebhookEnvelope.schema.json digest 73072d5268ce580486e5695822e9fa458e3a04a2804cdac22ab90ca4a74052d6 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const W_E_B_H_O_O_KE_N_V_E_L_O_P_E_SCHEMA_DIGEST = '73072d5268ce580486e5695822e9fa458e3a04a2804cdac22ab90ca4a74052d6';

export interface WebhookEnvelope {
  auth_verification: unknown;
  body_digest: string;
  connector_id: string;
  delivery_id: string;
  payload: object;
  received_at: string;
  schema_revision: unknown;
  tenant_id: string;
  webhook_id: string;
}
