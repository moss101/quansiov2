// Canonical contract binding for NotificationRecord.
// Generated from schemas/NotificationRecord.schema.json digest b6d5506724a27518e27847fa355aceddc417d8ab81ef2e232ef63007cb209bea by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const N_O_T_I_F_I_C_A_T_I_O_NR_E_C_O_R_D_SCHEMA_DIGEST = 'b6d5506724a27518e27847fa355aceddc417d8ab81ef2e232ef63007cb209bea';

export interface NotificationRecord {
  approval_request_id?: string | unknown | undefined;
  attention_type: string;
  created_at: string;
  deep_link_target: string;
  notification_id: string;
  recipient_id: string;
  schema_revision: unknown;
  state: unknown;
  tenant_id: string;
  urgency: unknown;
}
