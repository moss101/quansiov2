// Canonical contract binding for QualificationResult.
// Generated from schemas/QualificationResult.schema.json digest 5baf49a99105cd5343ea96606f5206f4543a76aa76c584b411bf0fcdeb8ee683 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const Q_U_A_L_I_F_I_C_A_T_I_O_NR_E_S_U_L_T_SCHEMA_DIGEST = '5baf49a99105cd5343ea96606f5206f4543a76aa76c584b411bf0fcdeb8ee683';

export interface QualificationResult {
  artifact_digests: object;
  assertion_results: unknown[];
  candidate_id: string;
  configuration_digest: string;
  executed_at: string;
  real_boundary: boolean;
  result_id: string;
  schema_revision: unknown;
  status: unknown;
  suite_id: string;
}
