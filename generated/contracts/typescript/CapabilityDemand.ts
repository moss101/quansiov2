// Canonical contract binding for CapabilityDemand.
// Generated from schemas/CapabilityDemand.schema.json digest 1784dd42f675ecda767fe99e4d5c74b1eb1f4f1a99243aea4aa11200ade7d05f by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const C_A_P_A_B_I_L_I_T_YD_E_M_A_N_D_SCHEMA_DIGEST = '1784dd42f675ecda767fe99e4d5c74b1eb1f4f1a99243aea4aa11200ade7d05f';

export interface CapabilityDemand {
  constraints: object;
  created_at: string;
  demand_id: string;
  dimensions: object;
  run_id: string;
  schema_revision: unknown;
  step_id: string;
  tenant_id: string;
}
