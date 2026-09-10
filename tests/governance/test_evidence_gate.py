"""GOV-006 acceptance tests: reproducible completion evidence.

Positive: PASS evidence validates only when task, requirement/assertion
coverage, reachable commit, report digest, artifact digests and real-boundary
proof all match actual state. Negative: outer PASS wrapping a blocking FAIL
and substituted artifact digests are rejected. Recovery: a genuine
unavailable boundary records BLOCKED_REAL_BOUNDARY and stays non-completing
until fresh PASS evidence is produced after the boundary becomes available.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts/validate_implementation_evidence.py"
TASKS = {t["task_id"]: t for t in json.loads((REPO_ROOT / "registries/tasks.json").read_text())}
REQS = {r["requirement_id"]: r for r in json.loads((REPO_ROOT / "registries/requirements.json").read_text())}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "qual@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "qualification"], check=True)
    (repo / "artifact.bin").write_bytes(b"qualification-artifact")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    return repo, commit


def write_evidence(repo: Path, commit: str, task_id: str = "GOV-006", *, status="PASS", assertion_override=None, real_boundary=False, artifact_bytes=b"qualification-artifact") -> Path:
    task = TASKS[task_id]
    task_aids = [a["assertion_id"] for a in task["assertions"] if a.get("blocking", True)]
    req_aids = [REQS[r]["assertion_id"] for r in task["requirement_ids"]]
    all_aids = task_aids + req_aids
    results = [
        {"assertion_id": aid, "blocking": True, "status": assertion_override.get(aid, "PASS") if assertion_override else "PASS"}
        for aid in all_aids
    ]
    (repo / "artifact.bin").write_bytes(artifact_bytes)
    report = {
        "schema_revision": "9.0.0",
        "report_id": "rep-qual",
        "task_id": task_id,
        "repository_id": "repo-qual",
        "git_commit": commit,
        "protected_ref": "HEAD",
        "environment_id": "env-qual",
        "configuration_digest": "0" * 64,
        "status": status,
        "assertion_results": results,
        "artifact_records": [
            {"path_or_uri": "artifact.bin", "digest": sha(repo / "artifact.bin"), "verification_method": "LOCAL_HASH", "verification_receipt_ref": None}
        ],
        "real_boundary": real_boundary,
        "executed_at": "2026-09-10T00:00:00Z",
    }
    report_path = repo / "report.json"
    report_path.write_text(json.dumps(report))
    evidence = {
        "schema_revision": "9.0.0",
        "evidence_id": "ev-qual",
        "task_id": task_id,
        "requirement_ids": sorted(task["requirement_ids"]),
        "task_assertion_ids": sorted(task_aids),
        "requirement_assertion_ids": sorted(req_aids),
        "repository_id": "repo-qual",
        "git_commit": commit,
        "report_path": "report.json",
        "report_digest": sha(report_path),
        "status": status,
        "real_boundary": real_boundary,
        "artifact_digests": {"artifact.bin": sha(repo / "artifact.bin")},
        "rollback_verified": True,
        "created_at": "2026-09-10T00:00:00Z",
    }
    evidence_path = repo / "evidence.json"
    evidence_path.write_text(json.dumps(evidence))
    return evidence_path


def validate(repo: Path, evidence_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--repo", str(repo), "--evidence", str(evidence_path), "--protected-ref", "HEAD"],
        capture_output=True,
        text=True,
    )


def test_p06_valid_evidence_passes(tmp_path):
    repo, commit = make_repo(tmp_path)
    result = validate(repo, write_evidence(repo, commit))
    assert result.returncode == 0, result.stdout + result.stderr


def test_p06_each_evidence_dimension_is_enforced(tmp_path):
    repo, commit = make_repo(tmp_path)

    # Unknown task.
    ev = write_evidence(repo, commit)
    data = json.loads(ev.read_text())
    data["task_id"] = "NOT-A-TASK"
    ev.write_text(json.dumps(data))
    assert validate(repo, ev).returncode != 0

    # Requirement coverage mismatch.
    ev = write_evidence(repo, commit)
    data = json.loads(ev.read_text())
    data["requirement_ids"] = data["requirement_ids"][:-1]
    ev.write_text(json.dumps(data))
    assert validate(repo, ev).returncode != 0

    # Task assertion coverage mismatch.
    ev = write_evidence(repo, commit)
    data = json.loads(ev.read_text())
    data["task_assertion_ids"] = data["task_assertion_ids"] + ["BOGUS-P99"]
    ev.write_text(json.dumps(data))
    assert validate(repo, ev).returncode != 0

    # Commit not reachable from protected ref (unrelated root).
    ev = write_evidence(repo, "f" * 40)
    assert validate(repo, ev).returncode != 0

    # Report digest mismatch.
    ev = write_evidence(repo, commit)
    report = json.loads((repo / "report.json").read_text())
    report["environment_id"] = "tampered"
    (repo / "report.json").write_text(json.dumps(report))
    assert validate(repo, ev).returncode != 0

    # Artifact digest mismatch (file substituted after evidence was written).
    ev = write_evidence(repo, commit)
    (repo / "artifact.bin").write_bytes(b"substituted-bytes")
    assert validate(repo, ev).returncode != 0

    # Real boundary required by task but evidence claims false.
    boundary_task = next(t["task_id"] for t in TASKS.values() if t.get("real_boundary_required"))
    repo2_commit = commit
    ev = write_evidence(repo, repo2_commit, task_id=boundary_task, real_boundary=False)
    assert validate(repo, ev).returncode != 0


def test_n06_outer_pass_cannot_wrap_blocking_fail(tmp_path):
    repo, commit = make_repo(tmp_path)
    ev = write_evidence(repo, commit, assertion_override={REQS["GOV-004"]["assertion_id"]: "FAIL"})
    result = validate(repo, ev)
    assert result.returncode != 0
    assert any("not PASS" in line for line in result.stdout.splitlines()), result.stdout


def test_n06_substituted_artifact_is_rejected(tmp_path):
    repo, commit = make_repo(tmp_path)
    ev = write_evidence(repo, commit)
    original = (repo / "artifact.bin").read_bytes()
    (repo / "artifact.bin").write_bytes(b"swapped after the fact")
    assert validate(repo, ev).returncode != 0
    (repo / "artifact.bin").write_bytes(original)
    assert validate(repo, ev).returncode == 0


def test_r06_blocked_boundary_stays_non_completing_until_boundary_available(tmp_path):
    repo, commit = make_repo(tmp_path)
    blocked = validate(repo, write_evidence(repo, commit, status="BLOCKED_REAL_BOUNDARY"))
    assert blocked.returncode == 2, blocked.stdout
    assert "BLOCKED_REAL_BOUNDARY" in blocked.stdout
    # The same blocked record still cannot close the task later.
    assert validate(repo, write_evidence(repo, commit, status="BLOCKED_REAL_BOUNDARY")).returncode == 2
    # Only fresh evidence produced after the boundary becomes available closes it.
    reopened = validate(repo, write_evidence(repo, commit, status="PASS"))
    assert reopened.returncode == 0, reopened.stdout
