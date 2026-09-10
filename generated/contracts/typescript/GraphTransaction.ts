// Canonical contract binding for GraphTransaction.
// Generated from schemas/GraphTransaction.schema.json digest f6f1a5e3bb6340e714fac8e00905e709ba1a3778374d78476746a20af692118e by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const G_R_A_P_HT_R_A_N_S_A_C_T_I_O_N_SCHEMA_DIGEST = 'f6f1a5e3bb6340e714fac8e00905e709ba1a3778374d78476746a20af692118e';

export interface GraphTransaction {
  expected_revision: number;
  idempotency_key: string;
  mutations: unknown[];
  run_id: string;
  schema_revision: unknown;
  tenant_id: string;
  transaction_id: string;
}
