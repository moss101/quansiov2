"""Milestone acceptance gate tests (GATE-M0, GATE-M1).

Positive: every blocking predecessor has valid evidence and the gate
evaluates PASS deterministically. Negative: removing one predecessor's
evidence makes the gate refuse advancement, naming the exact missing task.
Recovery: restoring the evidence re-evaluates the gate to PASS without
changing any other completed task evidence.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_TOOL = REPO_ROOT / "tools/governance/milestone_gate.py"
PY = sys.executable
GATES_UNDER_TEST = ["GATE-M0", "GATE-M1", "GATE-M2", "GATE-M3", "GATE-M4", "GATE-M5", "GATE-M6", "GATE-M7", "GATE-M8", "GATE-M9", "GATE-M10", "GATE-M11"]
EXPECTED_M0 = {"ENV-001", "GOV-001", "GOV-002", "GOV-003", "GOV-004", "GOV-005", "GOV-006", "GOV-007"}
EXPECTED_M1 = {"DAT-001", "DAT-002", "DAT-003", "DAT-004", "DAT-005", "DAT-006", "DAT-007", "DAT-008", "SEC-001", "GATE-M0"}
EXPECTED_M2 = {"RUN-001", "RUN-002", "RUN-003", "RUN-004", "RUN-005", "RUN-006", "RUN-007", "RUN-008", "GATE-M1"}
EXPECTED_M3 = {"MOD-001", "MOD-002", "MOD-003", "MOD-004", "MOD-005", "MOD-006", "MOD-007", "MOD-008", "GATE-M2"}
EXPECTED_M4 = {"CTX-001", "CTX-002", "CTX-003", "CTX-004", "CTX-005", "CTX-006", "CTX-007", "CTX-008", "GATE-M3"}
EXPECTED_M5 = {"SEC-002", "SEC-003", "SEC-004", "SEC-005", "EFF-001", "EFF-002", "EFF-003", "GATE-M4"}
EXPECTED_M6 = {"MAC-001", "MAC-002", "MAC-003", "MAC-004", "MAC-005", "MAC-006", "MAC-007", "MAC-008", "GATE-M5"}
EXPECTED_M7 = {"BRW-001", "BRW-002", "BRW-003", "BRW-004", "BRW-005", "BRW-006", "BRW-007", "BRW-008", "GATE-M6"}
EXPECTED_M8 = {"KNW-001", "KNW-002", "KNW-003", "SKL-001", "SKL-002", "SKL-003", "SKL-004", "SKL-005", "GATE-M7"}
EXPECTED_M9 = {"BUS-001", "BUS-002", "BUS-003", "BUS-004", "BUS-005", "EXT-001", "EXT-002", "EXT-003", "GATE-M8"}
EXPECTED_M10 = {"AUT-001", "AUT-002", "AUT-003", "AUT-004", "COL-001", "COL-002", "COL-003", "COL-004", "GATE-M9"}
EXPECTED_M11 = {"UX-001", "UX-002", "UX-003", "UX-004", "UX-005", "UX-006", "UX-007", "UX-008", "GATE-M10"}
EXPECTED_M12 = {"SRE-001", "SRE-002", "SRE-003", "SRE-004", "SRE-005", "SRE-006", "SEC-006", "SEC-007", "GATE-M11"}
EXPECTED = {"GATE-M0": EXPECTED_M0, "GATE-M1": EXPECTED_M1, "GATE-M2": EXPECTED_M2, "GATE-M3": EXPECTED_M3, "GATE-M4": EXPECTED_M4, "GATE-M5": EXPECTED_M5, "GATE-M6": EXPECTED_M6, "GATE-M7": EXPECTED_M7, "GATE-M8": EXPECTED_M8, "GATE-M9": EXPECTED_M9, "GATE-M10": EXPECTED_M10, "GATE-M11": EXPECTED_M11, "GATE-M12": EXPECTED_M12}
# a direct predecessor whose evidence removal must fail the gate
PROBE_PREDECESSOR = {"GATE-M0": "gov-003", "GATE-M1": "dat-003", "GATE-M2": "run-003", "GATE-M3": "mod-003", "GATE-M4": "ctx-003", "GATE-M5": "eff-003", "GATE-M6": "mac-003", "GATE-M7": "brw-003", "GATE-M8": "knw-003", "GATE-M9": "ext-003", "GATE-M10": "aut-003", "GATE-M11": "ux-002", "GATE-M12": "sre-003"}
PROBE_NAME = {"GATE-M0": "GOV-003", "GATE-M1": "DAT-003", "GATE-M2": "RUN-003", "GATE-M3": "MOD-003", "GATE-M4": "CTX-003", "GATE-M5": "EFF-003", "GATE-M6": "MAC-003", "GATE-M7": "BRW-003", "GATE-M8": "KNW-003", "GATE-M9": "EXT-003", "GATE-M10": "AUT-003", "GATE-M11": "UX-002", "GATE-M12": "SRE-003"}


def run_gate(*args: str, gate: str = "GATE-M0", out: Path | None = None) -> subprocess.CompletedProcess:
    extra = ["--out", str(out)] if out else []
    return subprocess.run(
        [PY, str(GATE_TOOL), "--gate", gate, *args, *extra], capture_output=True, text=True, cwd=REPO_ROOT
    )


def predecessor_index(report_path: Path) -> dict[str, str]:
    report = json.loads(report_path.read_text())
    return {entry["task"]: entry.get("evidence_digest") for entry in report["predecessor_evidence_index"]}


@pytest.fixture(params=GATES_UNDER_TEST)
def gate_report(tmp_path, request):
    out = tmp_path / f"{request.param}.json"
    result = run_gate("--write", out=out, gate=request.param)
    assert result.returncode == 0, result.stdout + result.stderr
    yield request.param, json.loads(out.read_text())


def test_gate_p01_all_predecessors_have_valid_evidence(gate_report):
    gate_id, report = gate_report
    assert report["result"] == "PASS"
    assert {e["task"] for e in report["predecessor_evidence_index"]} == EXPECTED[gate_id]
    for entry in report["predecessor_evidence_index"]:
        assert entry["status"] == "PASS", entry
        assert entry["evidence_digest"], entry


def test_gate_n01_missing_predecessor_refuses_advancement_with_task_identified(gate_report):
    gate_id, _report = gate_report
    evidences = sorted((REPO_ROOT / "evidence/reports").glob(f"evidence-{PROBE_PREDECESSOR[gate_id]}-*.json"))
    stash_dir = REPO_ROOT / "evidence/reports/.stash"
    stash_dir.mkdir(exist_ok=True)
    moved = []
    for evidence in evidences:
        target = stash_dir / evidence.name
        shutil.move(str(evidence), str(target))
        moved.append((target, evidence))
    try:
        result = run_gate(gate=gate_id)
        assert result.returncode != 0
        assert PROBE_NAME[gate_id] in result.stdout
        assert "no completion evidence" in result.stdout
    finally:
        for target, evidence in moved:
            shutil.move(str(target), str(evidence))
        stash_dir.rmdir()
    restored = run_gate(gate=gate_id)
    assert restored.returncode == 0, restored.stdout


def test_gate_r01_restored_gate_matches_prior_evaluation_without_touching_other_evidence(gate_report, tmp_path):
    gate_id, committed_report = gate_report
    before = {e["task"]: e.get("evidence_digest") for e in committed_report["predecessor_evidence_index"]}
    probe = PROBE_PREDECESSOR[gate_id]
    evidences = sorted((REPO_ROOT / "evidence/reports").glob(f"evidence-{probe}-*.json"))
    stash_dir = REPO_ROOT / "evidence/reports/.stash"
    stash_dir.mkdir(exist_ok=True)
    moved = []
    for evidence in evidences:
        target = stash_dir / evidence.name
        shutil.move(str(evidence), str(target))
        moved.append((target, evidence))
    try:
        assert run_gate(gate=gate_id).returncode != 0
    finally:
        for target, evidence in moved:
            shutil.move(str(target), str(evidence))
        stash_dir.rmdir()
    out = tmp_path / f"{gate_id}-after.json"
    assert run_gate("--write", out=out, gate=gate_id).returncode == 0
    after = predecessor_index(out)
    # Deterministic re-evaluation: identical verdict inputs, other tasks untouched.
    assert before == after
    # Verify each predecessor's evidence file still hashes to the recorded digest.
    report = json.loads(out.read_text())
    for entry in report["predecessor_evidence_index"]:
        path = REPO_ROOT / entry["evidence"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry["evidence_digest"], entry
