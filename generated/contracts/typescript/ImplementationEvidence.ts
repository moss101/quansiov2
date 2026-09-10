// Canonical contract binding for ImplementationEvidence.
// Generated from schemas/ImplementationEvidence.schema.json digest 6ced0e8298bfd6ddb215224cb87ce31f0dd21c8e17cfb02403799c89a29c17fd by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const I_M_P_L_E_M_E_N_T_A_T_I_O_NE_V_I_D_E_N_C_E_SCHEMA_DIGEST = '6ced0e8298bfd6ddb215224cb87ce31f0dd21c8e17cfb02403799c89a29c17fd';

export interface ImplementationEvidence {
  artifact_digests: object;
  created_at: string;
  evidence_id: string;
  git_commit: string;
  real_boundary: boolean;
  report_digest: string;
  report_path: string;
  repository_id: string;
  requirement_assertion_ids: unknown[];
  requirement_ids: unknown[];
  rollback_verified?: boolean | undefined;
  schema_revision: unknown;
  status: unknown;
  task_assertion_ids: unknown[];
  task_id: string;
}
