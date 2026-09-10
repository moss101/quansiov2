// Canonical contract binding for ContextProjection.
// Generated from schemas/ContextProjection.schema.json digest ca274a9fb78d8d7c65b5ea852fddb04c19955209a726c336557bb0d9688086c1 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const C_O_N_T_E_X_TP_R_O_J_E_C_T_I_O_N_SCHEMA_DIGEST = 'ca274a9fb78d8d7c65b5ea852fddb04c19955209a726c336557bb0d9688086c1';

export interface ContextProjection {
  capability_snapshot_id?: string | undefined;
  content_blocks: unknown[];
  knowledge_refs: unknown[];
  privacy_decision_id?: string | undefined;
  projection_id: string;
  revision: number;
  run_id: string;
  schema_revision: unknown;
  source_refs: unknown[];
  step_id: string;
  tenant_id: string;
  token_budget: number;
}
