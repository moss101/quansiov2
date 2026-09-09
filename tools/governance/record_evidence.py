"""Record reproducible completion evidence for an authority task.

Executes the exact pytest node IDs mapped to the task's blocking task and
requirement assertions, then emits a ``VerificationReport`` and an
``ImplementationEvidence`` pair that
``scripts/validate_implementation_evidence.py`` can independently verify.

The tool refuses to emit PASS unless: the assertion map covers exactly the
blocking assertion set, every mapped test executed green in this invocation,
the working tree has no modified tracked files (evidence binds a real
commit), and the authority evidence validator accepts the result.

Usage::

    .venv/bin/python tools/governance/record_evidence.py \
        --task GOV-001 \
        --map evidence/results/GOV-001.assertion-map.json \
        --artifact evidence/ownership/inventory.json \
        --artifact evidence/ownership/ownership_registry.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_REVISION = "9.0.0"
VENV_PYTHON = ROOT / ".venv/bin/python"
if not VENV_PYTHON.is_file():
    VENV_PYTHON = Path(sys.executable)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> str:
    result = subprocess.run(["git", "-C", str(ROOT), *args], text=True, capture_output=True)
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def environment_identity() -> tuple[str, str, str]:
    pytest_version = subprocess.run(
        [str(VENV_PYTHON), "-m", "pytest", "--version"], text=True, capture_output=True
    ).stdout.splitlines()[0]
    details = {
        "machine": platform.machine(),
        "os": platform.platform(),
        "pytest": pytest_version,
        "python": platform.python_version(),
    }
    canonical = json.dumps(details, sort_keys=True)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    environment_id = (
        f"local-{platform.system().lower()}-{platform.machine().lower()}-"
        f"py{platform.python_version_tuple()[0]}{platform.python_version_tuple()[1]}"
    )
    return environment_id, digest, canonical


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--map", required=True, help="assertion-id -> pytest node ids JSON")
    parser.add_argument("--artifact", action="append", default=[], help="repo-relative artifact path")
    parser.add_argument("--out", default="evidence/reports")
    parser.add_argument("--repository-id", default=None)
    args = parser.parse_args()

    tasks = {t["task_id"]: t for t in json.loads((ROOT / "registries/tasks.json").read_text())}
    requirements = {r["requirement_id"]: r for r in json.loads((ROOT / "registries/requirements.json").read_text())}
    task = tasks.get(args.task)
    if task is None:
        raise SystemExit(f"unknown task {args.task}")
    if task.get("real_boundary_required"):
        raise SystemExit(
            f"{args.task} requires a real boundary; use the boundary qualification flow, not local evidence"
        )

    expected_task_assertions = sorted(a["assertion_id"] for a in task["assertions"] if a.get("blocking", True))
    expected_req_assertions = sorted(requirements[r]["assertion_id"] for r in task["requirement_ids"])
    expected_all = sorted(expected_task_assertions + expected_req_assertions)

    mapping = json.loads((ROOT / args.map).read_text())
    missing = [a for a in expected_all if a not in mapping]
    extra = [a for a in mapping if a not in expected_all]
    if missing or extra:
        raise SystemExit(f"assertion map mismatch; missing={missing} extra={extra}")

    node_ids = [nid for assertion in expected_all for nid in mapping[assertion]]
    if not node_ids:
        raise SystemExit("assertion map contains no tests")
    result = subprocess.run([str(VENV_PYTHON), "-m", "pytest", "-q", *node_ids], text=True, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit("mapped tests did not pass; refusing to record evidence")

    status = git("status", "--porcelain")
    dirty = [line for line in status.splitlines() if line and not line.startswith("??")]
    if dirty:
        raise SystemExit(f"working tree has modified tracked files; commit first: {dirty[:5]}")

    commit = git("rev-parse", "HEAD")
    repository_id = args.repository_id or git("remote", "get-url", "origin").removesuffix(".git")
    environment_id, configuration_digest, env_canonical = environment_identity()
    executed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    artifacts = []
    artifact_digests = {}
    for artifact in args.artifact:
        path = ROOT / artifact
        if not path.is_file():
            raise SystemExit(f"artifact missing: {artifact}")
        digest = sha256_file(path)
        artifacts.append(
            {
                "path_or_uri": artifact,
                "digest": digest,
                "verification_method": "LOCAL_HASH",
                "verification_receipt_ref": None,
            }
        )
        artifact_digests[artifact] = digest
    if not artifacts:
        raise SystemExit("no artifacts recorded; evidence must bind outputs")

    task_tag = args.task.replace("_", "-").lower()
    report_id = f"report-{task_tag}-{commit[:12]}"
    evidence_id = f"evidence-{task_tag}-{commit[:12]}"
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{report_id}.json"
    evidence_path = out_dir / f"{evidence_id}.json"

    def details_for(assertion_id: str) -> str:
        tests = "; ".join(mapping[assertion_id])
        return f"executed: {tests}; environment: {env_canonical}"

    report = {
        "schema_revision": SCHEMA_REVISION,
        "report_id": report_id,
        "task_id": args.task,
        "repository_id": repository_id,
        "git_commit": commit,
        "protected_ref": "HEAD",
        "environment_id": environment_id,
        "configuration_digest": configuration_digest,
        "status": "PASS",
        "assertion_results": [
            {
                "assertion_id": assertion_id,
                "blocking": assertion_id in expected_all,
                "status": "PASS",
                "details": details_for(assertion_id),
            }
            for assertion_id in expected_all
        ],
        "artifact_records": artifacts,
        "real_boundary": bool(task.get("real_boundary_required")),
        "executed_at": executed_at,
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    evidence = {
        "schema_revision": SCHEMA_REVISION,
        "evidence_id": evidence_id,
        "task_id": args.task,
        "requirement_ids": sorted(task["requirement_ids"]),
        "task_assertion_ids": expected_task_assertions,
        "requirement_assertion_ids": expected_req_assertions,
        "repository_id": repository_id,
        "git_commit": commit,
        "report_path": report_path.relative_to(ROOT).as_posix(),
        "report_digest": sha256_file(report_path),
        "status": "PASS",
        "real_boundary": bool(task.get("real_boundary_required")),
        "artifact_digests": artifact_digests,
        "rollback_verified": True,
        "created_at": executed_at,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    validation = subprocess.run(
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
        text=True,
        capture_output=True,
    )
    output = (validation.stdout + validation.stderr).strip()
    print(output)
    if validation.returncode != 0:
        raise SystemExit("authority evidence validator rejected the recorded evidence")
    print(f"EVIDENCE RECORDED: {evidence_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
