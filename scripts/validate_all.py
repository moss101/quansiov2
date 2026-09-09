#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
steps=['validate_contracts.py','validate_authority.py','self_test_validators.py']
if (ROOT/'MANIFEST.json').exists(): steps.append('validate_integrity.py')
for s in steps:
 r=subprocess.run([sys.executable,str(ROOT/'scripts'/s)])
 if r.returncode: raise SystemExit(r.returncode)
print('ALL AUTHORITY CHECKS: PASS')
