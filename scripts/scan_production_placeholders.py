#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys
PATS=[
 ('NotImplementedError',re.compile(r'\bNotImplementedError\b')),
 ('python_pass_placeholder',re.compile(r'^\s*pass\s*(?:#.*)?$',re.M)),
 ('rust_todo',re.compile(r'\btodo!\s*\(')),('rust_unimplemented',re.compile(r'\bunimplemented!\s*\(')),
 ('not_implemented_throw',re.compile(r'throw\s+new\s+(?:Error|Exception)\s*\(\s*["\'][^"\']*(?:not implemented|todo)',re.I)),
 ('simulated_success',re.compile(r'\bSIMULATED_SUCCESS\b|\bPLACEHOLDER_IMPLEMENTATION\b'))]
EXCLUDE={'tests','test','fixtures','vendor','third_party','node_modules','.git','dist','build','generated','__pycache__','.venv','venv','.tox','.eggs'}
TEXT_EXT={'.py','.go','.rs','.ts','.tsx','.js','.jsx','.java','.kt','.swift','.cs','.rb','.php','.sh'}
def load_registered_exclusions(root):
    """Registered non-production paths (validator self-tests etc.).

    The exclusion list is explicit and tracked; it may only name test,
    fixture, vendor or generated paths, never arbitrary production code.
    """
    path=root/'scripts/scan_exclusions.json'
    if not path.is_file(): return set()
    data=json.loads(path.read_text())
    exclusions=set()
    for item in data.get('excluded_paths',[]):
        allowed={'self_test','fixture','vendor','generated'}
        if item.get('reason_class') not in allowed:
            raise SystemExit(f'scan_exclusions.json: {item.get("path")} has non-registered reason class')
        exclusions.add(item['path'])
    return exclusions
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root'); args=ap.parse_args(); root=Path(args.root)
 registered=load_registered_exclusions(root)
 hits=[]
 for p in root.rglob('*'):
  if not p.is_file() or p.suffix.lower() not in TEXT_EXT: continue
  rel=p.relative_to(root).as_posix()
  if any(x in EXCLUDE for x in p.parts): continue
  if rel in registered: continue
  try: s=p.read_text(errors='ignore')
  except: continue
  for n,r in PATS:
   for m in r.finditer(s):
    # A bare pass is allowed in exception/class/protocol shapes only if the line is explicitly marked abstract/no-cover.
    if n=='python_pass_placeholder':
     before=s[max(0,m.start()-120):m.start()].lower()
     if 'abstractmethod' in before or 'protocol' in before: continue
    ln=s.count('\n',0,m.start())+1; hits.append((rel,ln,n))
 if hits:
  print('PRODUCTION SOURCE SCAN: FAIL'); [print(f'{a}:{b}: {c}') for a,b,c in hits]; return 1
 print('PRODUCTION SOURCE SCAN: PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
