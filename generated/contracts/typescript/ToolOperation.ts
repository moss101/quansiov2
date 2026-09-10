// Canonical contract binding for ToolOperation.
// Generated from schemas/ToolOperation.schema.json digest 7f82baadb986d6d7ec34b36275c30e41d1c84623acd8b3f9fdde99d3f1b46957 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const T_O_O_LO_P_E_R_A_T_I_O_N_SCHEMA_DIGEST = '7f82baadb986d6d7ec34b36275c30e41d1c84623acd8b3f9fdde99d3f1b46957';

export interface ToolOperation {
  capability_requirements: unknown[];
  effect_class: unknown;
  evidence_requirements: unknown[];
  fidelity: unknown;
  idempotency: unknown;
  input_schema_id: string;
  operation_id: string;
  output_schema_id: string;
  policy_requirements?: unknown[] | undefined;
  schema_revision: unknown;
  timeout_ms: number;
  version: string;
}
