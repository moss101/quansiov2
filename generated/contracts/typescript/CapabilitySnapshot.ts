// Canonical contract binding for CapabilitySnapshot.
// Generated from schemas/CapabilitySnapshot.schema.json digest aab310403d833a8134ca483f39762adf11a4e94b3fb7b4c8473c49e1aa37b657 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const C_A_P_A_B_I_L_I_T_YS_N_A_P_S_H_O_T_SCHEMA_DIGEST = 'aab310403d833a8134ca483f39762adf11a4e94b3fb7b4c8473c49e1aa37b657';

export interface CapabilitySnapshot {
  actor_id: string;
  atoms: unknown[];
  capability_snapshot_id: string;
  constraints: object;
  expires_at: string;
  issued_at: string;
  parent_snapshot_id?: string | unknown | undefined;
  schema_revision: unknown;
  tenant_id: string;
}
