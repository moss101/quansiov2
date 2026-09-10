// Canonical contract binding for KnowledgeCandidate.
// Generated from schemas/KnowledgeCandidate.schema.json digest 96483a2254dca34682b3879ecee51e46dcf8a7c9bcc7b02135d40f9598ef1b4b by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const K_N_O_W_L_E_D_G_EC_A_N_D_I_D_A_T_E_SCHEMA_DIGEST = '96483a2254dca34682b3879ecee51e46dcf8a7c9bcc7b02135d40f9598ef1b4b';

export interface KnowledgeCandidate {
  candidate_id: string;
  confidence: number;
  conflict_refs?: unknown[] | undefined;
  evidence_refs: unknown[];
  knowledge_type: string;
  provenance: object;
  schema_revision: unknown;
  source_epoch: number;
  status: unknown;
  tenant_id: string;
  valid_from: string;
  valid_until?: string | unknown | undefined;
}
