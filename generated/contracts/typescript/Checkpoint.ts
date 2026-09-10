// Canonical contract binding for Checkpoint.
// Generated from schemas/Checkpoint.schema.json digest 026460248d64e14f478907fa41378199556b8293ff58740691250557cc9a4c01 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const C_H_E_C_K_P_O_I_N_T_SCHEMA_DIGEST = '026460248d64e14f478907fa41378199556b8293ff58740691250557cc9a4c01';

export interface Checkpoint {
  artifact_manifest_digest: string;
  checkpoint_id: string;
  created_at: string;
  database_position: string;
  event_sequence: number;
  execution_generation: number;
  schema_revision: unknown;
  snapshot_digest: string;
  state: unknown;
  target_id: string;
  tenant_id: string;
  tier: unknown;
}
