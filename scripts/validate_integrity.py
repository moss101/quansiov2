#!/usr/bin/env python3
from pathlib import Path
import json, hashlib, sys, re
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED_FROM_MANIFEST={'MANIFEST.json','V9_SPECIFICATION_SEAL.md','VALIDATION_REPORT.md','CHECKSUMS.sha256'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
errs=[]
manifest=json.load(open(ROOT/'MANIFEST.json'))
entries=manifest.get('files',[])
paths=[x.get('path') for x in entries]
if len(paths)!=len(set(paths)): errs.append('manifest contains duplicate paths')
if set(paths)&EXCLUDED_FROM_MANIFEST: errs.append('manifest contains circular/excluded integrity artifacts')
actual_payload=sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p.relative_to(ROOT).as_posix() not in EXCLUDED_FROM_MANIFEST and '__pycache__' not in p.parts)
if sorted(paths)!=actual_payload:
 missing=sorted(set(actual_payload)-set(paths)); extra=sorted(set(paths)-set(actual_payload))
 errs.append(f'manifest coverage mismatch missing={missing} extra={extra}')
if manifest.get('file_count')!=len(entries): errs.append('manifest file_count mismatch')
for x in entries:
 p=ROOT/x['path']
 if not p.is_file(): errs.append(f'missing manifest file {x["path"]}')
 else:
  if sha(p)!=x.get('sha256'): errs.append(f'manifest digest mismatch {x["path"]}')
  if p.stat().st_size!=x.get('size_bytes'): errs.append(f'manifest size mismatch {x["path"]}')
md=sha(ROOT/'MANIFEST.json')
seal=(ROOT/'V9_SPECIFICATION_SEAL.md').read_text()
if md not in seal: errs.append('specification seal does not bind current manifest digest')
# Seal counts must match canonical registries/schemas.
tasks=json.load(open(ROOT/'registries/tasks.json')); reqs=json.load(open(ROOT/'registries/requirements.json')); schemas=list((ROOT/'schemas').glob('*.schema.json'))
for label,value in [('Canonical tasks',len(tasks)),('Normative requirements',len(reqs)),('Canonical schemas',len(schemas))]:
 if f'**{label}:** {value}' not in seal: errs.append(f'seal {label.lower()} count mismatch')
# CHECKSUMS must cover every file except itself, exactly once.
checks={}
for line in (ROOT/'CHECKSUMS.sha256').read_text().splitlines():
 if not line.strip(): continue
 try: digest,path=line.split('  ',1)
 except ValueError: errs.append(f'malformed checksum line: {line}'); continue
 if path in checks: errs.append(f'duplicate checksum path {path}')
 checks[path]=digest
expected_checks=sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p.name!='CHECKSUMS.sha256' and '__pycache__' not in p.parts)
if sorted(checks)!=expected_checks:
 errs.append(f'checksum coverage mismatch missing={sorted(set(expected_checks)-set(checks))} extra={sorted(set(checks)-set(expected_checks))}')
for path,digest in checks.items():
 p=ROOT/path
 if not p.is_file() or sha(p)!=digest: errs.append(f'checksum mismatch {path}')
if errs:
 print('INTEGRITY VALIDATION: FAIL'); [print('- '+e) for e in errs]; sys.exit(1)
print(f'INTEGRITY VALIDATION: PASS ({len(entries)} manifest payload files, {len(checks)} checksummed files)')
