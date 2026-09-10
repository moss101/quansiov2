// Canonical contract binding for ReleaseStateRecord.
// Generated from schemas/ReleaseStateRecord.schema.json digest 5a66b48351608cfeef8c2348922b9c2a509e891bcc1ac591957cc67a57dbb498 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const R_E_L_E_A_S_ES_T_A_T_ER_E_C_O_R_D_SCHEMA_DIGEST = '5a66b48351608cfeef8c2348922b9c2a509e891bcc1ac591957cc67a57dbb498';

export interface ReleaseStateRecord {
  candidate_id: string;
  created_at: string;
  evidence_refs: unknown[];
  from_state: string | unknown;
  owner_task_id: string;
  record_id: string;
  schema_revision: unknown;
  to_state: unknown;
}
