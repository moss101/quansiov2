"""GOV-005 acceptance tests: production-source completeness scan.

Positive: the scanner fails on reachable incomplete implementation markers
in the production tree while excluding only registered test, fixture, vendor
and generated paths. Negative: an incomplete branch behind a reachable API
path fails the scan even when task metadata claims PASS. Recovery: the same
marker inside an isolated test fixture keeps production scanning clean
without broadening exclusions.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNER = REPO_ROOT / "scripts/scan_production_placeholders.py"


def run_scan(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCANNER), str(root)], capture_output=True, text=True)


def write(tmp_path: Path, rel: str, text: str) -> Path:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


PROD_MARKER = "def handle(request):\n    raise NotImplementedError()\n"


def test_p05_fails_on_production_marker(tmp_path):
    write(tmp_path, "quansio/runtime/worker.py", PROD_MARKER)
    assert run_scan(tmp_path).returncode != 0


def test_p05_excludes_only_registered_classes(tmp_path):
    write(tmp_path, "quansio/runtime/worker.py", "def handle(request):\n    return request\n")
    for rel in (
        "tests/test_marker.py",
        "tests/fixtures/marker.py",
        "vendor/lib/marker.py",
        "third_party/lib/marker.py",
        "node_modules/pkg/marker.js",
        "generated/contracts/marker.py",
    ):
        write(tmp_path, rel, PROD_MARKER)
    result = run_scan(tmp_path)
    assert result.returncode == 0, result.stdout


def test_p05_live_repo_scan_is_clean():
    result = run_scan(REPO_ROOT)
    assert result.returncode == 0, result.stdout


def test_p05_unregistered_exclusion_reason_class_is_rejected(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/scan_exclusions.json").write_text(
        json.dumps({"excluded_paths": [{"path": "quansio/danger.py", "reason_class": "convenience"}]})
    )
    write(tmp_path, "quansio/danger.py", PROD_MARKER)
    result = run_scan(tmp_path)
    assert result.returncode != 0
    assert "non-registered reason class" in result.stdout + result.stderr


def test_n05_reachable_api_marker_fails_despite_pass_metadata(tmp_path):
    write(
        tmp_path,
        "services/quansio_api/main.py",
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/runs/{run_id}')\n"
        "def get_run(run_id: str):\n"
        "    raise NotImplementedError  # reachable API path\n",
    )
    metadata = write(
        tmp_path,
        "evidence/reports/fake-pass.json",
        json.dumps({"task_id": "RUN-001", "status": "PASS", "assertion_results": [{"assertion_id": "RUN-001-P01", "status": "PASS", "blocking": True}]}),
    )
    assert json.loads(metadata.read_text())["status"] == "PASS"
    result = run_scan(tmp_path)
    assert result.returncode != 0
    assert "services/quansio_api/main.py" in result.stdout


def test_r05_marker_in_test_fixture_keeps_production_clean(tmp_path):
    write(tmp_path, "tests/fixtures/isolated/marker_fixture.py", PROD_MARKER)
    write(tmp_path, "quansio/runtime/worker.py", "def handle(request):\n    return dispatch(request)\n")
    result = run_scan(tmp_path)
    assert result.returncode == 0, result.stdout
    exclusions = json.loads((REPO_ROOT / "scripts/scan_exclusions.json").read_text())["excluded_paths"]
    assert all(item["path"] != "tests/fixtures/isolated/marker_fixture.py" for item in exclusions), (
        "fixture exclusion was broadened to accept the marker"
    )
