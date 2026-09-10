// Canonical contract binding for PolicyDecision.
// Generated from schemas/PolicyDecision.schema.json digest 1ecbd62bb617564957d4f2ad77443a3fc432b4f3bf159f51c1c4daf12fecb1c3 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const P_O_L_I_C_YD_E_C_I_S_I_O_N_SCHEMA_DIGEST = '1ecbd62bb617564957d4f2ad77443a3fc432b4f3bf159f51c1c4daf12fecb1c3';

export interface PolicyDecision {
  actor_id: string;
  argument_scope_digest: string;
  capability_snapshot_id: string;
  data_classification: unknown[];
  decision: unknown;
  expires_at: string;
  operation_id: string;
  policy_decision_id: string;
  policy_revision: string;
  schema_revision: unknown;
  target_scope: object;
  tenant_id: string;
}
