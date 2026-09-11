"""Refresh stale completion evidence across the whole task DAG.

For every recorded task (any ``evidence/results/<TASK>.assertion-map.json``),
re-validates its latest evidence against the current tree and re-records the
evidence for tasks whose bound artifacts drifted. Tasks are processed in
milestone order so gate reports are refreshed after their predecessors.

Usage::

    .venv/bin/python tools/governance/refresh_evidence.py            # re-record stale
    .venv/bin/python tools/governance/refresh_evidence.py --check    # report only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "evidence/reports"
RESULTS = ROOT / "evidence/results"
VENV = ROOT / ".venv/bin/python"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def latest_evidence(task_id: str) -> Path | None:
    """Newest evidence for a task, ordered by the recorded created_at
    timestamp (filename hex is a commit prefix and does not sort
    chronologically)."""
    candidates = sorted(REPORTS.glob(f"evidence-{task_id.lower()}-*.json"))

    def created_at(path: Path) -> str:
        try:
            return json.loads(path.read_text()).get("created_at", "")
        except (OSError, ValueError):
            return ""

    return max(candidates, key=created_at) if candidates else None


def is_stale(evidence_path: Path) -> bool:
    evidence = json.loads(evidence_path.read_text())
    for artifact, digest in evidence.get("artifact_digests", {}).items():
        path = ROOT / artifact
        if not path.is_file() or sha(path) != digest:
            return True
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/validate_implementation_evidence.py"),
            "--repo", str(ROOT),
            "--evidence", str(evidence_path),
            "--protected-ref", "HEAD",
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode != 0


def record(task: str, artifacts: list[str], boundary_manifest: Path | None) -> tuple[int, str]:
    cmd = [str(VENV), "tools/governance/record_evidence.py", "--task", task,
           "--map", f"evidence/results/{task}.assertion-map.json"]
    if boundary_manifest is not None:
        cmd += ["--boundary-manifest", str(boundary_manifest)]
    for artifact in artifacts:
        cmd += ["--artifact", artifact]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    lines = (result.stdout + result.stderr).strip().splitlines()
    return result.returncode, (lines[-1] if lines else "?"),


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--boundary-manifest", default=None)
    args = parser.parse_args()

    artifacts_map = json.loads((RESULTS / "artifacts.json").read_text())
    tasks = json.loads((ROOT / "registries/tasks.json").read_text())
    milestone = {t["task_id"]: t["milestone"] for t in tasks}
    boundary = Path(args.boundary_manifest) if args.boundary_manifest else None

    recorded = []
    for map_path in sorted(RESULTS.glob("*.assertion-map.json")):
        task_id = map_path.name.removesuffix(".assertion-map.json")
        evidence = latest_evidence(task_id)
        if evidence is None:
            continue
        recorded.append((milestone.get(task_id, 99), task_id, evidence))

    stale = []
    for _m, task_id, evidence in recorded:
        if is_stale(evidence):
            stale.append(task_id)
        else:
            print(f"fresh    {task_id}")

    if args.check or not stale:
        print(f"REFRESH: {len(stale)} stale of {len(recorded)} recorded tasks" + (" (stale: " + ", ".join(stale) + ")" if stale else ""))
        return 0

    print(f"REFRESH: re-recording {len(stale)} stale tasks: {', '.join(stale)}")
    failures = 0
    def sort_key(entry):
        m, task_id, _e = entry
        return (m, task_id.startswith("GATE-"), task_id)
    for _m, task_id, _evidence in sorted(
        ((m, t, e) for m, t, e in recorded if t in stale), key=sort_key
    ):
        artifacts = artifacts_map.get(task_id, [])
        need_boundary = json.loads((ROOT / "registries/tasks.json").read_text())
        boundary_required = next(
            t.get("real_boundary_required", False) for t in need_boundary if t["task_id"] == task_id
        )
        if boundary_required and boundary is None:
            r = subprocess.run([str(VENV), "tools/environment/qualenv.py", "provision"],
                               capture_output=True, text=True, cwd=ROOT)
            if r.returncode != 0:
                print(f"{task_id}: provision failed: {r.stdout} {r.stderr}")
                failures += 1
                continue
            boundary = sorted((ROOT / "evidence/environment").glob("*/manifest.json"))[-1]
        code, message = record(task_id, artifacts, boundary if boundary_required else None)
        print(f"{task_id}: rc={code} {message}")
        failures += code != 0
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
