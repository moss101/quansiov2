// Canonical contract binding for RecoveryConsistencyPoint.
// Generated from schemas/RecoveryConsistencyPoint.schema.json digest 60d7b9f10aa0da84ed3f1d0602780272e16da26bccdb8c40e4e7363ae5789a2d by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const R_E_C_O_V_E_R_YC_O_N_S_I_S_T_E_N_C_YP_O_I_N_T_SCHEMA_DIGEST = '60d7b9f10aa0da84ed3f1d0602780272e16da26bccdb8c40e4e7363ae5789a2d';

export interface RecoveryConsistencyPoint {
  created_at: string;
  database_position: string;
  effect_settlement_watermark: string;
  evidence_manifest_digest: string;
  recovery_point_id: string;
  runtime_event_sequence: number;
  schema_revision: unknown;
  snapshot_inventory_digest: string;
  unresolved_unknown_effect_ids: unknown[];
}
