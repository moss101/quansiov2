// Canonical contract binding for AutomationFire.
// Generated from schemas/AutomationFire.schema.json digest 400dcaef59f6ebcaa878b584c93e7d7ae2472937d1114ab6063549310098387d by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const A_U_T_O_M_A_T_I_O_NF_I_R_E_SCHEMA_DIGEST = '400dcaef59f6ebcaa878b584c93e7d7ae2472937d1114ab6063549310098387d';

export interface AutomationFire {
  attempt: number;
  authority_snapshot_id: string;
  automation_id: string;
  fire_id: string;
  logical_fire_key: string;
  run_id?: string | unknown | undefined;
  scheduled_for: string;
  schema_revision: unknown;
  state: unknown;
  tenant_id: string;
}
