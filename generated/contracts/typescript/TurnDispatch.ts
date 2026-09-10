// Canonical contract binding for TurnDispatch.
// Generated from schemas/TurnDispatch.schema.json digest a59f8aceca55327a858c0d83e9be99982604a922d219fb94c14012e941da727b by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const T_U_R_ND_I_S_P_A_T_C_H_SCHEMA_DIGEST = 'a59f8aceca55327a858c0d83e9be99982604a922d219fb94c14012e941da727b';

export interface TurnDispatch {
  cancellation_id?: string | unknown | undefined;
  capability_snapshot_id: string;
  deadline: string;
  dispatch_id: string;
  expected_output_schema_id: string;
  idempotency_key: string;
  input_refs: unknown[];
  parent_run_id: string;
  parent_turn_id: string;
  schema_revision: unknown;
  target_agent_id: string;
  tenant_id: string;
}
