// Canonical contract binding for BudgetReservation.
// Generated from schemas/BudgetReservation.schema.json digest 0d1c2463a8dc6c99f4d1c2eaea2bc3b7289e7596454c05d61c733e2754382e89 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const B_U_D_G_E_TR_E_S_E_R_V_A_T_I_O_N_SCHEMA_DIGEST = '0d1c2463a8dc6c99f4d1c2eaea2bc3b7289e7596454c05d61c733e2754382e89';

export interface BudgetReservation {
  amount: number;
  idempotency_key: string;
  kind: unknown;
  parent_reservation_id?: string | unknown | undefined;
  reservation_id: string;
  run_id: string;
  schema_revision: unknown;
  state: unknown;
  tenant_id: string;
}
