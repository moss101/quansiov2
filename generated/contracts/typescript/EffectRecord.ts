// Canonical contract binding for EffectRecord.
// Generated from schemas/EffectRecord.schema.json digest b34515c9dc93e983e1b257b21193189c3c37e081b87e9981fc23bae0dbe1c518 by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const E_F_F_E_C_TR_E_C_O_R_D_SCHEMA_DIGEST = 'b34515c9dc93e983e1b257b21193189c3c37e081b87e9981fc23bae0dbe1c518';

export interface EffectRecord {
  approval_receipt_id?: string | unknown | undefined;
  argument_scope_digest: string;
  created_at: string;
  effect_class: unknown;
  effect_id: string;
  evidence_refs?: unknown[] | undefined;
  idempotency_key: string;
  operation_id: string;
  policy_decision_id: string;
  receipt_ref?: string | unknown | undefined;
  run_id: string;
  schema_revision: unknown;
  state: unknown;
  step_id: string;
  tenant_id: string;
}
