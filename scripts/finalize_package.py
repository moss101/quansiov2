#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/governance'))
from repo_paths import iter_payload_files, sha256_file  # noqa: E402
EXCLUDED={'MANIFEST.json','V9_SPECIFICATION_SEAL.md','VALIDATION_REPORT.md','CHECKSUMS.sha256'}
def run(script):
 r=subprocess.run([sys.executable,str(ROOT/'scripts'/script)],capture_output=True,text=True)
 if r.returncode:
  sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); raise SystemExit(r.returncode)
 return (r.stdout+r.stderr).strip()
# Canonical generated views first.
r=subprocess.run([sys.executable,str(ROOT/'scripts/regenerate_authority_views.py'),'--write'],capture_output=True,text=True)
if r.returncode: print(r.stdout+r.stderr); raise SystemExit(r.returncode)
outputs={}
for s in ['validate_contracts.py','validate_authority.py','self_test_validators.py']:
 outputs[s]=run(s)
tasks=json.load(open(ROOT/'registries/tasks.json')); reqs=json.load(open(ROOT/'registries/requirements.json')); edges=json.load(open(ROOT/'registries/task-graph.json'))['edges']; schemas=list((ROOT/'schemas').glob('*.schema.json'))
report=['# Validation Report','','**Schema revision:** `9.0.0`','',f'**Tasks:** {len(tasks)}  ',f'**Requirements:** {len(reqs)}  ',f'**Schemas:** {len(schemas)}  ',f'**Dependency edges:** {len(edges)}','', '## Executed authority checks','']
for s,out in outputs.items():
 report += [f'### `{s}`','', 'Exit code: `0`','', '```text',out,'```','']
report += ['## Integrity model','','`MANIFEST.json` hashes every payload file except the four integrity/reporting artifacts that would create circularity: `MANIFEST.json`, `V9_SPECIFICATION_SEAL.md`, `VALIDATION_REPORT.md`, and `CHECKSUMS.sha256`. The specification seal binds the manifest digest. `CHECKSUMS.sha256` covers every package file except itself. `scripts/validate_integrity.py` enforces exact coverage, digests, sizes and seal counts.','','The packaging pipeline runs `validate_integrity.py` after writing the manifest, seal and checksums. Its executed result is emitted by the finalization command rather than embedded here, so the report bytes remain stable after sealing.','']
(ROOT/'VALIDATION_REPORT.md').write_text('\n'.join(report))
# Manifest payload after report has been written; report remains outside manifest by design.
payload=[]
for p in iter_payload_files(ROOT):
 rel=p.relative_to(ROOT).as_posix()
 if rel in EXCLUDED: continue
 payload.append({'path':rel,'sha256':sha256_file(p),'size_bytes':p.stat().st_size})
manifest={'authority_name':'Quansio V9 Final Implementation Authority','schema_revision':'9.0.0','file_count':len(payload),'files':payload}
(ROOT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
md=sha256_file(ROOT/'MANIFEST.json')
seal=f'''# Quansio V9 Specification Seal\n\n**Schema revision:** `9.0.0`  \n**Manifest SHA-256:** `{md}`  \n**Canonical tasks:** {len(tasks)}  \n**Normative requirements:** {len(reqs)}  \n**Canonical schemas:** {len(schemas)}  \n**Dependency edges:** {len(edges)}\n\nThis seal binds the exact non-circular authority payload listed by `MANIFEST.json`. The manifest excludes itself, this seal, `VALIDATION_REPORT.md` and `CHECKSUMS.sha256`. `CHECKSUMS.sha256` then covers every package file except itself.\n'''
(ROOT/'V9_SPECIFICATION_SEAL.md').write_text(seal)
# Exact checksums for every payload file except checksum file itself.
lines=[]
for p in iter_payload_files(ROOT):
 if p.name=='CHECKSUMS.sha256': continue
 lines.append(f'{sha256_file(p)}  {p.relative_to(ROOT).as_posix()}')
(ROOT/'CHECKSUMS.sha256').write_text('\n'.join(lines)+'\n')
# Final integrity validation.
out=run('validate_integrity.py')
print('FINALIZATION: PASS')
for s,v in outputs.items(): print(v)
print(out)
print('Manifest SHA-256:',md)
