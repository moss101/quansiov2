// Canonical contract binding for EndpointActionResult.
// Generated from schemas/EndpointActionResult.schema.json digest a635bb039f3983140532816e234496dce44fe388fe079f692acd9454f3970372 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const E_N_D_P_O_I_N_TA_C_T_I_O_NR_E_S_U_L_T_SCHEMA_DIGEST = 'a635bb039f3983140532816e234496dce44fe388fe079f692acd9454f3970372';

export interface EndpointActionResult {
  action_id: string;
  completed_at: string;
  delivery_id: string;
  evidence_refs?: unknown[] | undefined;
  execution_generation: number;
  result: object;
  schema_revision: unknown;
  status: unknown;
  target_id: string;
}
