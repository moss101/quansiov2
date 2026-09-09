#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
def render_plan(tasks):
 out=['# 19 — Implementation plan','','The machine-readable task DAG is canonical. This view is generated from it.','']
 for m in sorted({t['milestone'] for t in tasks}):
  title='Post-readiness production promotion' if m==15 else f'Milestone M{m}'
  ms=[t for t in tasks if t['milestone']==m]; out += [f'## {title}',f'**Tasks:** {len(ms)}','']
  for t in ms: out.append(f"- `{t['task_id']}` — {t['title']} — deps: {', '.join(t['depends_on']) if t['depends_on'] else 'none'}")
  out.append('')
 return '\n'.join(out).strip()+'\n'
def render_tasks(tasks):
 out=['# 20 — Atomic task registry','','Generated from `registries/tasks.json`.','']
 for t in sorted(tasks,key=lambda x:(x['milestone'],x['task_id'])):
  out += [f"## {t['task_id']} — {t['title']}",f"- Milestone: {t['milestone']}",f"- Owner: {t['owner']}",f"- Requirements: {', '.join(t['requirement_ids'])}",f"- Dependencies: {', '.join(t['depends_on']) if t['depends_on'] else 'none'}",f"- Real boundary required: {str(t['real_boundary_required']).lower()}",'- Assertions:']
  for a in t['assertions']: out.append(f"  - **{a['assertion_id']} [{a['kind']}]** — {a['text']}")
  out += [f"- Required evidence: {', '.join(t['evidence_required'])}",f"- Forbidden shortcuts: {', '.join(t['forbidden_shortcuts'])}",'']
 return '\n'.join(out).strip()+'\n'
def render_reqs(reqs):
 out=['# 34 — Normative requirements','','| Requirement | Domain | Assertion | Normative statement | Linked tasks |','|---|---|---|---|---|']
 for r in sorted(reqs,key=lambda x:x['requirement_id']): out.append(f"| {r['requirement_id']} | {r['domain']} | {r['assertion_id']} | {r['statement']} | {', '.join(r['task_ids'])} |")
 return '\n'.join(out)+'\n'
def render_master():
 sources=['00_README.md','AGENTS.md','HANDOFF.md','INSTALL.md','SKILLS.md','TOOLS.md']
 sources += [str(x.relative_to(ROOT)) for x in sorted((ROOT/'docs').glob('*.md'))]
 out=['# Quansio V9 Final Master Dossier','','**Schema revision:** `9.0.0`','','This is the consolidated reading copy. Canonical registries and schemas remain machine-readable authority.','']
 for rel in sources:
  p=ROOT/rel
  if not p.exists(): continue
  out += ['','---','',f'<!-- source: {rel} -->','',p.read_text().rstrip(),'']
 return '\n'.join(out).rstrip()+'\n'
def expected():
 tasks=json.load(open(ROOT/'registries/tasks.json')); reqs=json.load(open(ROOT/'registries/requirements.json'))
 return {'docs/19_IMPLEMENTATION_PLAN.md':render_plan(tasks),'docs/20_ATOMIC_TASK_REGISTRY.md':render_tasks(tasks),'docs/34_REQUIREMENT_REGISTRY.md':render_reqs(reqs),'Quansio_V9_FINAL_MASTER_DOSSIER.md':render_master()}
def main():
 mode='--write' if '--write' in sys.argv else '--check'
 bad=[]
 for rel,text in expected().items():
  p=ROOT/rel
  if mode=='--write': p.write_text(text)
  elif not p.exists() or p.read_text()!=text: bad.append(rel)
 if bad: print('GENERATED VIEW CHECK: FAIL'); [print('- '+x) for x in bad]; return 1
 print('GENERATED VIEW '+('WRITE' if mode=='--write' else 'CHECK')+': PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
