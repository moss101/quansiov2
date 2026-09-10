// Canonical contract binding for RuntimeEvent.
// Generated from schemas/RuntimeEvent.schema.json digest 3cca01f30c04b71c7ef49f22b50fce726d5656b98c262ede5989ee50272e682b by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const R_U_N_T_I_M_EE_V_E_N_T_SCHEMA_DIGEST = '3cca01f30c04b71c7ef49f22b50fce726d5656b98c262ede5989ee50272e682b';

export interface RuntimeEvent {
  causal_parent_ids?: unknown[] | undefined;
  committed_at: string;
  event_id: string;
  event_type: string;
  execution_generation: number;
  occurred_at: string;
  payload: object;
  producer_id: string;
  producer_sequence?: number | undefined;
  run_id: string;
  schema_revision: unknown;
  sequence: number;
  tenant_id: string;
  workspace_id: string;
}
