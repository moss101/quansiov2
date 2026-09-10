// Canonical contract binding for RemoteArtifactVerification.
// Generated from schemas/RemoteArtifactVerification.schema.json digest 1cf8923b193018441bab1350ee6859786282eea1b4cd842454f3edeabcd34538 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const R_E_M_O_T_EA_R_T_I_F_A_C_TV_E_R_I_F_I_C_A_T_I_O_N_SCHEMA_DIGEST = '1cf8923b193018441bab1350ee6859786282eea1b4cd842454f3edeabcd34538';

export interface RemoteArtifactVerification {
  attestation_digest?: string | unknown | undefined;
  attestation_path?: string | unknown | undefined;
  environment_id: string;
  expected_digest: string;
  observed_at: string;
  observed_digest: string;
  path_or_uri: string;
  schema_revision: unknown;
  status: unknown;
  verification_id: string;
  verification_method: unknown;
  verifier_identity: string;
}
