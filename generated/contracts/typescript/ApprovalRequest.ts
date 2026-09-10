// Canonical contract binding for ApprovalRequest.
// Generated from schemas/ApprovalRequest.schema.json digest fea463bcacddade1edea5b9adb3e046bf7b011c39bb595779b87e247f16c930b by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const A_P_P_R_O_V_A_LR_E_Q_U_E_S_T_SCHEMA_DIGEST = 'fea463bcacddade1edea5b9adb3e046bf7b011c39bb595779b87e247f16c930b';

export interface ApprovalRequest {
  approval_request_id: string;
  argument_scope_digest: string;
  data_classification?: unknown[] | undefined;
  effect_id: string;
  expires_at: string;
  financial_scope?: object | unknown | undefined;
  operation_id: string;
  requested_authority: unknown[];
  risk_class: string;
  schema_revision: unknown;
  target: object;
  tenant_id: string;
}
