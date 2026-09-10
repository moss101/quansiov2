// Canonical contract binding for CommandEnvelope.
// Generated from schemas/CommandEnvelope.schema.json digest 88350b175833c113fbaea76b18c272b5fbd0feb5c153d7a57f2811fd8fed1da6 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const C_O_M_M_A_N_DE_N_V_E_L_O_P_E_SCHEMA_DIGEST = '88350b175833c113fbaea76b18c272b5fbd0feb5c153d7a57f2811fd8fed1da6';

export interface CommandEnvelope {
  actor_id: string;
  arguments: object;
  command_id: string;
  command_type: string;
  idempotency_key: string;
  schema_revision: unknown;
  submitted_at: string;
  tenant_id: string;
  workspace_id: string;
}
