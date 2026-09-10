// Canonical contract binding for SkillPackage.
// Generated from schemas/SkillPackage.schema.json digest 2355abbb698156f21d00c9d619842adc55124442725c3510b1ebb1e68ceabda1 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const S_K_I_L_LP_A_C_K_A_G_E_SCHEMA_DIGEST = '2355abbb698156f21d00c9d619842adc55124442725c3510b1ebb1e68ceabda1';

export interface SkillPackage {
  assets?: unknown[] | undefined;
  capability_requirements: unknown[];
  compatibility?: object | undefined;
  dependencies: unknown[];
  evaluation_thresholds: object;
  exclusions: unknown[];
  helpers?: unknown[] | undefined;
  input_contract: object;
  instructions: unknown[];
  intended_use: unknown[];
  output_contract: object;
  owner_scope: string;
  promotion_state: unknown;
  purpose: string;
  rollback_target: string | unknown;
  schema_revision: unknown;
  skill_id: string;
  source_refs: unknown[];
  version: string;
}
