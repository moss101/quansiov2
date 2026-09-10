#!/usr/bin/env bash
# Full repository verification: authority views, integrity artifacts,
# authority validators, ownership inventory, production source scan, tests.
set -euo pipefail
cd "$(dirname "$0")/../.."
PY="${PY:-python3}"
VENV_PY=".venv/bin/python"

echo "== authority generation (write then deterministic check) =="
"$PY" tools/governance/generate_authority.py --write
"$PY" tools/governance/generate_authority.py --check

echo "== ownership inventory =="
"$PY" tools/governance/ownership_inventory.py

echo "== authority map =="
"$PY" tools/governance/ownership_map.py

echo "== contract gate =="
"$PY" tools/governance/contract_gate.py

echo "== production source scan =="
"$PY" scripts/scan_production_placeholders.py .

echo "== test suites =="
"$VENV_PY" -m pytest tests/ -q

echo "VERIFY ALL: PASS"
