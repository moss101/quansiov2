"""Milestone acceptance gate evaluation (GATE-M*).

Evaluates a milestone gate task (e.g. ``GATE-M0``) by independently
re-validating the completion evidence of every blocking predecessor:

- each predecessor must have recorded evidence under ``evidence/reports/``;
- the authority evidence validator must accept that evidence against the
  current protected ref (commit reachability, report digest, assertion
  coverage, artifact digests, real-boundary proof).

Cross-milestone qualification suites are intentionally not enforced here:
they are qualified by the QA-* vertical tasks (milestone M13) and the
support profile ``enabled_when`` rules, not by milestone task gates.

The result is written to ``evidence/gates/<GATE>-json`` with the exact
missing task/assertion identified on failure, so gate advancement cannot be
manually bypassed.

Usage::

    python tools/governance/milestone_gate.py --gate GATE-M0 [--write]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "evidence/reports"
GATES_DIR = ROOT / "evidence/gates"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evidence_for_task(task_id: str) -> Path | None:
    candidates = sorted(REPORTS_DIR.glob(f"evidence-{task_id.lower()}-*.json"))
    if not candidates:
        return None
    # Prefer the evidence whose bound commit is the newest descendant.
    newest = candidates[0]
    for candidate in candidates[1:]:
        try:
            commit_new = json.loads(candidate.read_text()).get("git_commit", "")
            commit_old = json.loads(newest.read_text()).get("git_commit", "")
        except json.JSONDecodeError:
            continue
        if commit_new and commit_old:
            descendant = subprocess.run(
                ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", commit_old, commit_new],
                capture_output=True,
            )
            if descendant.returncode == 0:
                newest = candidate
    return newest


def validate_evidence(evidence_path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/validate_implementation_evidence.py"),
            "--repo",
            str(ROOT),
            "--evidence",
            str(evidence_path),
            "--protected-ref",
            "HEAD",
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def evaluate(gate_id: str) -> dict:
    tasks = {t["task_id"]: t for t in json.loads((ROOT / "registries/tasks.json").read_text())}
    gate = tasks.get(gate_id)
    if gate is None:
        raise SystemExit(f"unknown gate {gate_id}")

    predecessors = sorted(gate["depends_on"])
    index = []
    problems = []
    for predecessor in predecessors:
        evidence_path = evidence_for_task(predecessor)
        if evidence_path is None:
            problems.append(
                {"task": predecessor, "reason": "no completion evidence recorded; task may not close the milestone"}
            )
            index.append({"task": predecessor, "evidence": None, "status": "MISSING"})
            continue
        evidence = json.loads(evidence_path.read_text())
        ok, detail = validate_evidence(evidence_path)
        status = evidence.get("status")
        if not ok:
            problems.append(
                {"task": predecessor, "reason": f"evidence validation failed: {detail.splitlines()[:4]}"}
            )
            index.append(
                {
                    "task": predecessor,
                    "evidence": evidence_path.relative_to(ROOT).as_posix(),
                    "evidence_digest": sha256_file(evidence_path),
                    "status": status or "INVALID",
                }
            )
            continue
        index.append(
            {
                "task": predecessor,
                "evidence": evidence_path.relative_to(ROOT).as_posix(),
                "evidence_digest": sha256_file(evidence_path),
                "status": status,
            }
        )

    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    repository_id = subprocess.run(
        ["git", "-C", str(ROOT), "remote", "get-url", "origin"], capture_output=True, text=True, check=True
    ).stdout.strip().removesuffix(".git")

    return {
        "schema_revision": "9.0.0",
        "gate": gate_id,
        "repository_id": repository_id,
        "git_commit": commit,
        "protected_ref": "HEAD",
        "result": "PASS" if not problems else "FAIL",
        "problems": problems,
        "predecessor_evidence_index": index,
        "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    report = evaluate(args.gate)
    out_path = GATES_DIR / f"{args.gate}.json"
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered)
    if report["result"] != "PASS":
        print(f"MILESTONE GATE {args.gate}: FAIL")
        for problem in report["problems"]:
            print(f"- {problem['task']}: {problem['reason']}")
        return 1
    if not args.write:
        print(f"MILESTONE GATE {args.gate}: PASS (report not written; use --write)")
        return 0
    print(f"MILESTONE GATE {args.gate}: PASS ({len(report['predecessor_evidence_index'])} predecessors validated; {out_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
