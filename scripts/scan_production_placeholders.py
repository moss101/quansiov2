#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys
PATS=[
 ('NotImplementedError',re.compile(r'\bNotImplementedError\b')),
 ('python_pass_placeholder',re.compile(r'^\s*pass\s*(?:#.*)?$',re.M)),
 ('rust_todo',re.compile(r'\btodo!\s*\(')),('rust_unimplemented',re.compile(r'\bunimplemented!\s*\(')),
 ('not_implemented_throw',re.compile(r'throw\s+new\s+(?:Error|Exception)\s*\(\s*["\'][^"\']*(?:not implemented|todo)',re.I)),
 ('simulated_success',re.compile(r'\bSIMULATED_SUCCESS\b|\bPLACEHOLDER_IMPLEMENTATION\b'))]
EXCLUDE={'tests','test','fixtures','vendor','third_party','node_modules','.git','dist','build','generated','__pycache__'}
TEXT_EXT={'.py','.go','.rs','.ts','.tsx','.js','.jsx','.java','.kt','.swift','.cs','.rb','.php','.sh'}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root'); args=ap.parse_args(); root=Path(args.root)
 hits=[]
 for p in root.rglob('*'):
  if not p.is_file() or p.suffix.lower() not in TEXT_EXT: continue
  if any(x in EXCLUDE for x in p.relative_to(root).parts): continue
  try: s=p.read_text(errors='ignore')
  except: continue
  for n,r in PATS:
   for m in r.finditer(s):
    # A bare pass is allowed in exception/class/protocol shapes only if the line is explicitly marked abstract/no-cover.
    if n=='python_pass_placeholder':
     line=s[m.start():m.end()]
     before=s[max(0,m.start()-120):m.start()].lower()
     if 'abstractmethod' in before or 'protocol' in before: continue
    ln=s.count('\n',0,m.start())+1; hits.append((str(p.relative_to(root)),ln,n))
 if hits:
  print('PRODUCTION SOURCE SCAN: FAIL'); [print(f'{a}:{b}: {c}') for a,b,c in hits]; return 1
 print('PRODUCTION SOURCE SCAN: PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
