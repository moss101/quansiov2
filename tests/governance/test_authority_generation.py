"""GOV-004 acceptance tests: deterministic authority generation.

Positive: regenerating task graph, inverse requirement links, milestone
counts, reading views, support mappings and integrity metadata twice yields
byte-identical outputs and check mode passes. Negative: hand-editing a
generated task edge or milestone count fails check mode. Recovery: deleting
a generated view and rerunning generation restores it solely from canonical
registries.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools/governance"))

import generate_authority  # noqa: E402

GENERATOR = REPO_ROOT / "tools/governance/generate_authority.py"


def run_generator(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GENERATOR), *args], capture_output=True, text=True, cwd=REPO_ROOT)


def test_p04_regeneration_twice_is_byte_identical():
    first = generate_authority.build_outputs()
    second = generate_authority.build_outputs()
    assert first == second
    assert run_generator("--check").returncode == 0


def test_p04_all_declared_derived_artifacts_are_regenerated():
    outputs = generate_authority.build_outputs()
    for rel in (
        "registries/task-graph.json",
        "registries/requirements.json",
        "docs/19_IMPLEMENTATION_PLAN.md",
        "docs/20_ATOMIC_TASK_REGISTRY.md",
        "docs/34_REQUIREMENT_REGISTRY.md",
        "Quansio_V9_FINAL_MASTER_DOSSIER.md",
        "generated/authority/support-mappings.md",
    ):
        assert rel in outputs, f"{rel} is not regenerated from canonical registries"


def test_p04_write_then_check_leaves_clean_tree():
    assert run_generator("--write").returncode == 0
    assert run_generator("--check").returncode == 0
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO_ROOT)
    dirty = [line for line in status.stdout.splitlines() if line and not line.startswith("??")]
    assert dirty == [], f"deterministic write left modified files: {dirty[:5]}"


def test_n04_hand_edited_task_edge_fails_check():
    graph_path = REPO_ROOT / "registries/task-graph.json"
    original = graph_path.read_bytes()
    try:
        graph = json.loads(original)
        graph["edges"][0]["from"] = "ROGUE-000"
        graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n")
        assert run_generator("--check").returncode != 0
    finally:
        graph_path.write_bytes(original)
    assert run_generator("--check").returncode == 0


def test_n04_hand_edited_milestone_count_fails_check():
    plan_path = REPO_ROOT / "docs/19_IMPLEMENTATION_PLAN.md"
    original = plan_path.read_bytes()
    try:
        mutated = original.replace(b"**Tasks:** 9", b"**Tasks:** 8", 1)
        assert mutated != original
        plan_path.write_bytes(mutated)
        assert run_generator("--check").returncode != 0
    finally:
        plan_path.write_bytes(original)
    assert run_generator("--check").returncode == 0


def test_r04_deleted_generated_view_is_restored_from_registries():
    view_path = REPO_ROOT / "docs/34_REQUIREMENT_REGISTRY.md"
    expected = generate_authority.build_outputs()["docs/34_REQUIREMENT_REGISTRY.md"]
    assert view_path.exists()
    view_path.unlink()
    assert not view_path.exists()
    assert run_generator("--write").returncode == 0
    assert view_path.read_text() == expected
    assert run_generator("--check").returncode == 0
