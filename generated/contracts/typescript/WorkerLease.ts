// Canonical contract binding for WorkerLease.
// Generated from schemas/WorkerLease.schema.json digest 23ab3234e98a9c643eb07a406fe85498fbfae43253c8dfc17749f87d16e5548f by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const W_O_R_K_E_RL_E_A_S_E_SCHEMA_DIGEST = '23ab3234e98a9c643eb07a406fe85498fbfae43253c8dfc17749f87d16e5548f';

export interface WorkerLease {
  execution_generation: number;
  expires_at: string;
  fence_token: number;
  issued_at: string;
  lease_id: string;
  run_id: string;
  schema_revision: unknown;
  state: unknown;
  target_id: string;
  tenant_id: string;
  worker_id: string;
}
