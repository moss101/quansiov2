// Canonical contract binding for AutomationSchedule.
// Generated from schemas/AutomationSchedule.schema.json digest 257f1b0db5188865620c3599e96e7ee80ec7f57c9f7c5062be90f8777c99dda6 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const A_U_T_O_M_A_T_I_O_NS_C_H_E_D_U_L_E_SCHEMA_DIGEST = '257f1b0db5188865620c3599e96e7ee80ec7f57c9f7c5062be90f8777c99dda6';

export interface AutomationSchedule {
  automation_id: string;
  dst_fold_policy: unknown;
  dst_gap_policy: unknown;
  max_catch_up: number;
  missed_fire_policy: unknown;
  owner_agent_id: string;
  rule: string;
  schema_revision: unknown;
  state: unknown;
  tenant_id: string;
  timezone: string;
}
