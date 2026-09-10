// Canonical contract binding for ApprovalReceipt.
// Generated from schemas/ApprovalReceipt.schema.json digest 044356c3fd75a043f7ddb13bbe1975d75d6fee6eefd2cc5b92939285524886a2 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const A_P_P_R_O_V_A_LR_E_C_E_I_P_T_SCHEMA_DIGEST = '044356c3fd75a043f7ddb13bbe1975d75d6fee6eefd2cc5b92939285524886a2';

export interface ApprovalReceipt {
  approval_receipt_id: string;
  approval_request_id: string;
  approver_id: string;
  argument_scope_digest: string;
  decided_at: string;
  decision: unknown;
  effect_id: string;
  schema_revision: unknown;
  tenant_id: string;
}
