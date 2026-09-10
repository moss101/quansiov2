// Canonical contract binding for VerificationReport.
// Generated from schemas/VerificationReport.schema.json digest bde578d2c069cda00da1c4bc2ae07de54cb90f42600bfeb42f6b09e4557dd731 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const V_E_R_I_F_I_C_A_T_I_O_NR_E_P_O_R_T_SCHEMA_DIGEST = 'bde578d2c069cda00da1c4bc2ae07de54cb90f42600bfeb42f6b09e4557dd731';

export interface VerificationReport {
  artifact_records: unknown[];
  assertion_results: unknown[];
  ci_pipeline_id?: string | undefined;
  ci_run_id?: string | undefined;
  configuration_digest: string;
  environment_id: string;
  executed_at: string;
  git_commit: string;
  protected_ref: string;
  real_boundary: boolean;
  report_id: string;
  repository_id: string;
  schema_revision: unknown;
  status: unknown;
  task_id: string;
}
