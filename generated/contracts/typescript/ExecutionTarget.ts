// Canonical contract binding for ExecutionTarget.
// Generated from schemas/ExecutionTarget.schema.json digest 7727b782fefb2972b2b0519b9039c7366847822fe1ac12c09bdfab0abd657d13 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const E_X_E_C_U_T_I_O_NT_A_R_G_E_T_SCHEMA_DIGEST = '7727b782fefb2972b2b0519b9039c7366847822fe1ac12c09bdfab0abd657d13';

export interface ExecutionTarget {
  execution_generation: number;
  fence_token?: number | unknown | undefined;
  health_state: string;
  lease_id?: string | unknown | undefined;
  lifecycle_state: unknown;
  schema_revision: unknown;
  support_profile_id: string;
  target_id: string;
  target_type: unknown;
  tenant_id: string;
}
