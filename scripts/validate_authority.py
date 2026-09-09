#!/usr/bin/env python3
from pathlib import Path
import json, re, hashlib, sys, subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/governance'))
from repo_paths import iter_payload_files  # noqa: E402
PAYLOAD=[p for p in iter_payload_files(ROOT)]
errs=[]
tasks=json.load(open(ROOT/'registries/tasks.json')); reqs=json.load(open(ROOT/'registries/requirements.json')); graph=json.load(open(ROOT/'registries/task-graph.json')); supports=json.load(open(ROOT/'registries/support-matrix.json')); suites=json.load(open(ROOT/'registries/qualification-matrix.json')); release=json.load(open(ROOT/'registries/release-state-machine.json'))
T={t['task_id']:t for t in tasks}; R={r['requirement_id']:r for r in reqs}; S={s['suite_id']:s for s in suites}
# Unique IDs and exact inverse links
if len(T)!=len(tasks): errs.append('duplicate task IDs')
if len(R)!=len(reqs): errs.append('duplicate requirement IDs')
for t in tasks:
 for r in t['requirement_ids']:
  if r not in R: errs.append(f'{t["task_id"]}: unknown requirement {r}')
  elif t['task_id'] not in R[r]['task_ids']: errs.append(f'{t["task_id"]}<->{r}: inverse link missing')
 if len(t['assertions'])<3: errs.append(f'{t["task_id"]}: fewer than three assertions')
 aids=[a['assertion_id'] for a in t['assertions']]
 if len(aids)!=len(set(aids)): errs.append(f'{t["task_id"]}: duplicate assertion IDs')
 for a in t['assertions']:
  if len(a.get('text','').strip())<45: errs.append(f'{t["task_id"]}: assertion too vague {a["assertion_id"]}')
for r in reqs:
 if not r['task_ids']: errs.append(f'{r["requirement_id"]}: uncovered')
 for tid in r['task_ids']:
  if tid not in T or r['requirement_id'] not in T[tid]['requirement_ids']: errs.append(f'{r["requirement_id"]}<->{tid}: inverse mismatch')
# Acceptance-contract semantic specificity: non-gate tasks must not share normalized assertion text.
def _norm_assertion(s):
 s=s.lower()
 s=re.sub(r'\b(?:[a-z]{2,8}-\d{3}|gate-m\d+)\b','<id>',s)
 s=re.sub(r'\b\d+(?:\.\d+)?\b','<n>',s)
 return re.sub(r'\s+',' ',s).strip()
for kind in ('positive','negative','recovery'):
 seen={}
 for t in tasks:
  if t['task_id'].startswith('GATE-'): continue
  matches=[a for a in t['assertions'] if a.get('kind')==kind]
  if not matches:
   errs.append(f'{t["task_id"]}: missing {kind} assertion')
   continue
  for a in matches:
   key=_norm_assertion(a['text'])
   if key in seen:
    errs.append(f'{t["task_id"]}: templated {kind} assertion duplicates {seen[key]}')
   else:
    seen[key]=t['task_id']
# Dependencies and DAG
for t in tasks:
 for d in t['depends_on']:
  if d not in T: errs.append(f'{t["task_id"]}: unknown dependency {d}')
  elif T[d]['milestone']>t['milestone']: errs.append(f'{t["task_id"]}: depends on future milestone {d}')
# DFS cycle
state={}
def dfs(n,stack):
 if state.get(n)==1: errs.append('dependency cycle: '+' -> '.join(stack+[n])); return
 if state.get(n)==2:return
 state[n]=1
 for d in T[n]['depends_on']: dfs(d,stack+[n])
 state[n]=2
for n in T: dfs(n,[])
# Graph exact
expected_nodes=sorted(T); expected_edges=sorted([{'from':d,'to':t['task_id']} for t in tasks for d in t['depends_on']],key=lambda x:(x['from'],x['to']))
if graph.get('nodes')!=expected_nodes or graph.get('edges')!=expected_edges: errs.append('task graph differs from task registry')
# Gate closure
for m in range(15):
 gid=f'GATE-M{m}'; members=sorted(t['task_id'] for t in tasks if t['milestone']==m and t['task_id']!=gid); expected=members+([f'GATE-M{m-1}'] if m else [])
 if set(T[gid]['depends_on'])!=set(expected): errs.append(f'{gid}: incomplete/excess milestone dependency closure')
if T['REL-008']['depends_on']!=['GATE-M14'] or T['REL-008']['milestone']<=14: errs.append('production promotion must depend on readiness gate and remain post-readiness')
if release.get('production_ready_owner')!='GATE-M14': errs.append('GATE-M14 is not sole production-ready owner')
for tr in release.get('transitions',[]):
 if tr.get('to')=='PRODUCTION_READY' and tr.get('owner')!='GATE-M14': errs.append('another release transition owns PRODUCTION_READY')
# Security dependency order
if T['SEC-001']['milestone']>=T['RUN-002']['milestone']: errs.append('CapabilitySnapshot arrives too late for agent admission')
if 'SEC-001' not in T['RUN-002']['depends_on']: errs.append('RUN-002 lacks CapabilitySnapshot prerequisite')
if T['MOD-008']['milestone']<=T['MOD-006']['milestone'] and 'MOD-006' not in T['MOD-008']['depends_on']: errs.append('model real-boundary qualification lacks privacy prerequisite')
if 'EFF-001' not in T['BRW-003']['depends_on']: errs.append('browser consequential-effect classification lacks Effect Ledger prerequisite')
# Support mappings
for p in supports:
 if p['status'] not in {'REQUIRED_GA','DISABLED_UNTIL_QUALIFIED','UNSUPPORTED'}: errs.append(f'{p["profile_id"]}: invalid support state')
 if p['status']!='UNSUPPORTED' and p.get('enabled_when')!='ALL_REQUIRED_SUITES_PASS': errs.append(f'{p["profile_id"]}: unsafe enablement rule')
 for s in p.get('required_suites',[]):
  if s not in S: errs.append(f'{p["profile_id"]}: unknown suite {s}')
 for tid in p.get('qualification_tasks',[]):
  if tid not in T: errs.append(f'{p["profile_id"]}: unknown qualification task {tid}')
for s in suites:
 if not s.get('qualification_tasks'): errs.append(f'{s["suite_id"]}: no qualification tasks')
# Source-agnostic and no historical-version language. Construct terms to avoid putting blocked strings literally into normal text.
blocked=['V'+str(i) for i in range(1,9)] + ['Gro'+'k','Per'+'plexity','Wiki'+'Skills','reverse'+' engineering']
text_ext={'.md','.json','.txt','.py'}
for p in PAYLOAD:
 if p.suffix.lower() not in text_ext: continue
 rel=p.relative_to(ROOT).as_posix()
 if rel=='scripts/validate_authority.py': continue
 s=p.read_text(errors='ignore')
 for term in blocked:
  if re.search(r'(?<![A-Za-z0-9_])'+re.escape(term)+r'(?![A-Za-z0-9_])',s,re.I): errs.append(f'{rel}: forbidden historical/provenance term')
# No mandatory report signing language or signature fields. Statements that explicitly say signatures are not required are allowed.
for p in PAYLOAD:
 if p.suffix.lower() not in {'.md','.json','.txt'}: continue
 s=p.read_text(errors='ignore').lower()
 if 'signed verificationreport' in s or 'signed verification report' in s or 'signature_required' in s: errs.append(f'{p.relative_to(ROOT)}: obsolete signing gate language')
# Authority-local document references must resolve. Only canonical package path prefixes are checked;
# application source examples are deliberately excluded.
path_pat=re.compile(r'`((?:docs|schemas|registries|graphs|wiring|prompts|protocols|scripts|tests/fixtures)/[^`\s]+|(?:AGENTS|HANDOFF|INSTALL|SKILLS|TOOLS|VALIDATION_REPORT|V9_SPECIFICATION_SEAL|MANIFEST)\.(?:md|json))`')
for p in PAYLOAD:
 if p.suffix!='.md': continue
 s=p.read_text(errors='ignore')
 for ref in path_pat.findall(s):
  ref=ref.rstrip('.,;:)')
  if '*' in ref or '{' in ref or '<' in ref: continue
  if not (ROOT/ref).exists(): errs.append(f'{p.relative_to(ROOT)}: broken authority path {ref}')
# Counts in README
readme=(ROOT/'00_README.md').read_text()
if f'{len(tasks)} tasks' not in readme or f'{len(reqs)} requirements' not in readme or f'{len(list((ROOT/"schemas").glob("*.schema.json")))} canonical schemas' not in readme: errs.append('README counts stale')
# Generated views
r=subprocess.run([sys.executable,str(ROOT/'scripts/regenerate_authority_views.py'),'--check'],capture_output=True,text=True)
if r.returncode: errs.append('generated reading views stale')
if errs:
 print('AUTHORITY VALIDATION: FAIL'); [print('- '+e) for e in errs]; sys.exit(1)
print(f'AUTHORITY VALIDATION: PASS ({len(tasks)} tasks, {len(reqs)} requirements, {len(list((ROOT/"schemas").glob("*.schema.json")))} schemas, {len(expected_edges)} dependency edges)')
