// Canonical contract binding for BrowserSession.
// Generated from schemas/BrowserSession.schema.json digest 9b72938131d1e3a877d7e3173d8f4422cfff1b5942b114d288f39e92388efd4c by
// tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
export const B_R_O_W_S_E_RS_E_S_S_I_O_N_SCHEMA_DIGEST = '9b72938131d1e3a877d7e3173d8f4422cfff1b5942b114d288f39e92388efd4c';

export interface BrowserSession {
  browser_session_id: string;
  controller: unknown;
  created_at: string;
  current_url?: string | unknown | undefined;
  execution_generation: number;
  schema_revision: unknown;
  state: unknown;
  target_id: string;
  tenant_id: string;
  workspace_id: string;
}
