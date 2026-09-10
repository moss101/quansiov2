"""GATE-M0 acceptance tests: milestone acceptance gate.

Positive: every blocking predecessor has valid evidence and the gate
evaluates PASS deterministically. Negative: removing one predecessor's
evidence makes the gate refuse advancement, naming the exact missing task.
Recovery: restoring the evidence re-evaluates the gate to PASS without
changing any other completed task evidence.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_TOOL = REPO_ROOT / "tools/governance/milestone_gate.py"
PY = sys.executable


def run_gate(*args: str, out: Path | None = None) -> subprocess.CompletedProcess:
    extra = ["--out", str(out)] if out else []
    return subprocess.run([PY, str(GATE_TOOL), "--gate", "GATE-M0", *args, *extra], capture_output=True, text=True, cwd=REPO_ROOT)


def predecessor_index(report_path: Path) -> dict[str, str]:
    report = json.loads(report_path.read_text())
    return {entry["task"]: entry.get("evidence_digest") for entry in report["predecessor_evidence_index"]}


@pytest.fixture()
def gate_report(tmp_path):
    out = tmp_path / "GATE-M0.json"
    result = run_gate("--write", out=out)
    assert result.returncode == 0, result.stdout + result.stderr
    yield json.loads(out.read_text())


def test_gate_p01_all_predecessors_have_valid_evidence(gate_report):
    expected = {
        "ENV-001",
        "GOV-001",
        "GOV-002",
        "GOV-003",
        "GOV-004",
        "GOV-005",
        "GOV-006",
        "GOV-007",
    }
    assert gate_report["result"] == "PASS"
    assert {e["task"] for e in gate_report["predecessor_evidence_index"]} == expected
    for entry in gate_report["predecessor_evidence_index"]:
        assert entry["status"] == "PASS", entry
        assert entry["evidence_digest"], entry


def test_gate_n01_missing_predecessor_refuses_advancement_with_task_identified(gate_report):
    evidences = sorted((REPO_ROOT / "evidence/reports").glob("evidence-gov-003-*.json"))
    stash_dir = REPO_ROOT / "evidence/reports/.stash"
    stash_dir.mkdir(exist_ok=True)
    moved = []
    for evidence in evidences:
        target = stash_dir / evidence.name
        shutil.move(str(evidence), str(target))
        moved.append((target, evidence))
    try:
        result = run_gate()
        assert result.returncode != 0
        assert "GOV-003" in result.stdout
        assert "no completion evidence" in result.stdout
    finally:
        for target, evidence in moved:
            shutil.move(str(target), str(evidence))
        stash_dir.rmdir()
    restored = run_gate()
    assert restored.returncode == 0, restored.stdout


def test_gate_r01_restored_gate_matches_prior_evaluation_without_touching_other_evidence(gate_report, tmp_path):
    committed = json.loads((REPO_ROOT / "evidence/gates/GATE-M0.json").read_text())
    before = {entry["task"]: entry.get("evidence_digest") for entry in committed["predecessor_evidence_index"]}
    evidences = sorted((REPO_ROOT / "evidence/reports").glob("evidence-gov-005-*.json"))
    stash_dir = REPO_ROOT / "evidence/reports/.stash"
    stash_dir.mkdir(exist_ok=True)
    moved = []
    for evidence in evidences:
        target = stash_dir / evidence.name
        shutil.move(str(evidence), str(target))
        moved.append((target, evidence))
    try:
        assert run_gate().returncode != 0
    finally:
        for target, evidence in moved:
            shutil.move(str(target), str(evidence))
        stash_dir.rmdir()
    out = tmp_path / "GATE-M0-after.json"
    assert run_gate("--write", out=out).returncode == 0
    after = predecessor_index(out)
    # Deterministic re-evaluation: identical verdict inputs, other tasks untouched.
    assert before == after
    # verify each predecessor's evidence file still hashes to the recorded digest
    report = json.loads(out.read_text())
    import hashlib

    for entry in report["predecessor_evidence_index"]:
        path = REPO_ROOT / entry["evidence"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry["evidence_digest"], entry
