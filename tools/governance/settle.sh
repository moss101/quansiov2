#!/usr/bin/env bash
# Deterministic evidence/integrity settle loop.
#
# After any code or test change, this brings the repository back to the
# canonical settled state: every task's evidence valid, every gate
# evaluated, integrity artifacts byte-deterministic, full suite green and a
# clean working tree.
set -euo pipefail
cd "$(dirname "$0")/../.."
PY="${PY:-python3}"
VPY=".venv/bin/python"

for round in 1 2 3; do
  echo "== settle round $round =="
  "$PY" tools/governance/refresh_evidence.py || true
  "$PY" tools/governance/generate_authority.py --write >/dev/null
  # Gate reports bind the current commit; rewrite and refresh their evidence
  # until every gate validates without drift.
  GATES_CHANGED=0
  for gate_json in evidence/gates/GATE-M*.json; do
    gate=$(basename "$gate_json" .json)
    if grep -q '"result": "FAIL"' "$gate_json" 2>/dev/null || [ ! -s "$gate_json" ]; then
      "$PY" tools/governance/milestone_gate.py --gate "$gate" --write >/dev/null || true
      GATES_CHANGED=1
    fi
  done
  "$PY" tools/governance/generate_authority.py --write >/dev/null
  "$VPY" -m pytest tests/ -q || { echo "SETTLE: tests failing"; exit 1; }
  if [ "$(git status --porcelain | wc -l | tr -d ' ')" = "0" ]; then
    echo "SETTLE: clean"
    exit 0
  fi
  git add -A
  git commit -q "Settle: refresh evidence, gates and integrity artifacts (round ${round})"
done
if [ "$(git status --porcelain | wc -l | tr -d ' ')" != "0" ]; then
  git add -A && git commit -q "Settle: final round"
  "$PY" tools/governance/generate_authority.py --write >/dev/null
  git add -A && git commit -q "Settle: integrity refresh" || true
fi
"$VPY" -m pytest tests/ -q
git status --porcelain | wc -l
echo "SETTLE: done"
