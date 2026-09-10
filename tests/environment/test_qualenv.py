"""ENV-001 acceptance tests: real qualification environment.

These tests drive real Docker-provisioned PostgreSQL, Redis and MinIO
boundaries (never in-memory substitutes). They require the Docker daemon;
if it is unreachable the suite fails rather than silently skipping, because
no real-boundary evidence may be fabricated.

Positive: provision yields four real boundaries with isolated identities,
health checks pass. Negative: qualification refuses an environment whose
required boundary is replaced by an in-memory fake. Recovery: independent
dependency restarts are detected, connections recover, and teardown leaves
no falsely passing environment state.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
QUALENV = REPO_ROOT / "tools/environment/qualenv.py"
PY = sys.executable


def qualegv(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([PY, str(QUALENV), *args], capture_output=True, text=True)


def docker(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True)


@pytest.fixture(scope="module")
def environment():
    result = qualegv("provision")
    assert result.returncode == 0, result.stdout + result.stderr
    manifests = sorted((REPO_ROOT / "evidence/environment").glob("*/manifest.json"))
    manifest = json.loads(manifests[-1].read_text())
    yield manifest
    torn = qualegv("teardown")
    assert torn.returncode == 0, torn.stdout + torn.stderr


def _docker_available() -> bool:
    return docker("info", "--format", "{{.ServerVersion}}").returncode == 0


def test_p01_four_real_boundaries_healthy_with_isolated_identities(environment):
    classes = {b["class"]: b for b in environment["boundaries"]}
    assert set(classes) == {
        "relational_primary",
        "durable_event_transport",
        "non_authoritative_coordination",
        "artifact_object_store",
    }
    for boundary in classes.values():
        assert boundary["kind"] == "real", boundary
        assert boundary["endpoint"], boundary
    assert environment["isolated_identities"] is True
    assert environment["secrets_digest"]
    health = qualegv("health")
    assert health.returncode == 0, health.stdout + health.stderr
    verify = qualegv("verify")
    assert verify.returncode == 0, verify.stdout + verify.stderr


def test_n01_in_memory_substitution_is_refused(environment, tmp_path):
    fake = json.loads(json.dumps(environment))
    for boundary in fake["boundaries"]:
        if boundary["class"] == "durable_event_transport":
            boundary["kind"] = "memory"
            boundary["implementation"] = "in-process queue"
    fake_manifest = tmp_path / "manifest.json"
    fake_manifest.write_text(json.dumps(fake))
    result = subprocess.run([PY, str(QUALENV), "verify", "--manifest", str(fake_manifest)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "refuses non-real boundaries" in result.stdout

    sqlite_variant = json.loads(json.dumps(environment))
    for boundary in sqlite_variant["boundaries"]:
        if boundary["class"] == "relational_primary":
            boundary["implementation"] = "sqlite:///qual.db"
    sqlite_manifest = tmp_path / "sqlite.json"
    sqlite_manifest.write_text(json.dumps(sqlite_variant))
    result = subprocess.run([PY, str(QUALENV), "verify", "--manifest", str(sqlite_manifest)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "forbidden implementation" in result.stdout


def test_r01_dependency_restart_is_detected_and_recovered(environment):
    assert _docker_available()
    for container in ("quansio-qual-redis", "quansio-qual-postgres"):
        stop = docker("stop", container)
        assert stop.returncode == 0, stop.stderr
        during = qualegv("health")
        assert during.returncode != 0, f"{container}: health falsely passed while dependency was stopped"
        start = docker("start", container)
        assert start.returncode == 0, start.stderr
        import time

        deadline = time.time() + 60
        while time.time() < deadline:
            if qualegv("health").returncode == 0:
                break
            time.sleep(2)
        else:
            raise AssertionError(f"{container}: health did not recover after restart")
    verify = qualegv("verify")
    assert verify.returncode == 0


def test_r01_teardown_leaves_no_falsely_passing_state(environment):
    torn = qualegv("teardown")
    assert torn.returncode == 0, torn.stdout + torn.stderr
    after = qualegv("health")
    assert after.returncode != 0, "health passed after teardown"
    assert "torn down" in after.stdout
    probe = docker("inspect", "-f", "{{.State.Running}}", "quansio-qual-postgres")
    assert probe.returncode != 0 or probe.stdout.strip() in {"false", ""}, "postgres container still running after teardown"
