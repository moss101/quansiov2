// Canonical contract binding for ArtifactRecord.
// Generated from schemas/ArtifactRecord.schema.json digest 32c7fa65ac7e3365c175ae3dec35a05926b8f01e81323c1a98f79cffa0dce282 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const A_R_T_I_F_A_C_TR_E_C_O_R_D_SCHEMA_DIGEST = '32c7fa65ac7e3365c175ae3dec35a05926b8f01e81323c1a98f79cffa0dce282';

export interface ArtifactRecord {
  artifact_id: string;
  created_at: string;
  digest: string;
  grant_refs?: unknown[] | undefined;
  media_type: string;
  producer_ref: string;
  scan_state: unknown;
  schema_revision: unknown;
  size_bytes: number;
  tenant_id: string;
}
