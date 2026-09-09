#!/usr/bin/env python3
from pathlib import Path
import argparse, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args()
steps=[[sys.executable,str(ROOT/'scripts/scan_production_placeholders.py'),a.repo],[sys.executable,str(ROOT/'scripts/validate_authority.py')],[sys.executable,str(ROOT/'scripts/validate_contracts.py')]]
for cmd in steps:
 r=subprocess.run(cmd)
 if r.returncode: raise SystemExit(r.returncode)
print('IMPLEMENTATION COMPLETENESS GATE: PASS (authority/source level; task evidence and real-boundary suites remain independently required)')
