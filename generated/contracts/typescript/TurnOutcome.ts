// Canonical contract binding for TurnOutcome.
// Generated from schemas/TurnOutcome.schema.json digest 1c8dda3dedf5fcd560f362932f0b6b35292179d3bdaac05b13d1c9fa43c86dd1 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const T_U_R_NO_U_T_C_O_M_E_SCHEMA_DIGEST = '1c8dda3dedf5fcd560f362932f0b6b35292179d3bdaac05b13d1c9fa43c86dd1';

export interface TurnOutcome {
  completed_sequence: number;
  dispatch_id: string;
  effect_refs?: unknown[] | undefined;
  error?: object | unknown | undefined;
  evidence_refs?: unknown[] | undefined;
  result_ref?: string | unknown | undefined;
  schema_revision: unknown;
  status: unknown;
  worker_id: string;
}
