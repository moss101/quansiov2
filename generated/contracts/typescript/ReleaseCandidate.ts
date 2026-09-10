// Canonical contract binding for ReleaseCandidate.
// Generated from schemas/ReleaseCandidate.schema.json digest 904459696f2c6063216b045862ca483877790c3021c043386f10c2a1f990794a by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const R_E_L_E_A_S_EC_A_N_D_I_D_A_T_E_SCHEMA_DIGEST = '904459696f2c6063216b045862ca483877790c3021c043386f10c2a1f990794a';

export interface ReleaseCandidate {
  artifact_digests: object;
  candidate_id: string;
  configuration_digest: string;
  created_at: string;
  migration_set_digest: string;
  schema_revision: unknown;
  source_commit: string;
  state: unknown;
  support_selection_digest: string;
}
