"""GOV-001 acceptance tests: canonical ownership inventory.

Positive: deterministic inventory mapping every production path to exactly
one owner. Negative: unowned production paths are rejected. Recovery:
tracked-input change is detected as drift, regeneration returns to a clean
deterministic state.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools/governance"))

import ownership_inventory as inv  # noqa: E402


def test_p01_inventory_is_deterministic_and_fully_owned():
    resolved_a, errors_a = inv.validate()
    resolved_b, errors_b = inv.validate()
    assert errors_a == [] and errors_b == []
    assert inv.render(inv.build_inventory(resolved_a)) == inv.render(inv.build_inventory(resolved_b))
    known_owners = set(inv.json.loads(inv.REGISTRY_PATH.read_text())["canonical_services"]) | set(
        inv.json.loads(inv.REGISTRY_PATH.read_text())["supporting_owners"]
    )
    seen = set()
    for entry in resolved_a:
        key = (entry["kind"], entry["path"])
        assert key not in seen, f"duplicate ownership mapping: {key}"
        seen.add(key)
        assert entry["owner"] in known_owners, f"unregistered owner on {key}"
        assert entry["role"], f"missing role for {key}"


def test_p01_committed_inventory_matches_regenerated():
    resolved, errors = inv.validate()
    assert errors == []
    committed = inv.INVENTORY_PATH.read_text()
    assert committed == inv.render(inv.build_inventory(resolved))


def test_p01_every_canonical_service_has_adoption_plan():
    registry = json.loads(inv.REGISTRY_PATH.read_text())
    registered_paths = {e["path"] for e in registry["entries"]}
    for service, spec in registry["canonical_services"].items():
        assert spec["package"] in registered_paths, f"{service} has no registered package path"
        assert spec["deployable"] in registered_paths or f"{spec['deployable']}/main.py" in registered_paths, (
            f"{service} has no registered deployable"
        )


def test_n01_unregistered_entrypoint_is_rejected(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.md").write_text("x")
    (tmp_path / "services").mkdir()
    (tmp_path / "services" / "rogue").mkdir()
    (tmp_path / "services" / "rogue" / "main.py").write_text("print('rogue')\n")
    resolved, errors = inv.validate(root=tmp_path)
    assert any("UNOWNED PATH" in e and "services/rogue/main.py" in e for e in errors), errors


def test_n01_live_repo_rejects_unowned_entrypoint():
    rogue_dir = REPO_ROOT / "services" / "rogue_probe"
    rogue_dir.mkdir(parents=True, exist_ok=True)
    try:
        (rogue_dir / "main.py").write_text("print('unregistered probe')\n")
        _, errors = inv.validate()
        assert any("UNOWNED PATH" in e and "services/rogue_probe/main.py" in e for e in errors), errors
    finally:
        shutil.rmtree(rogue_dir)
        services_dir = REPO_ROOT / "services"
        if services_dir.is_dir() and not any(services_dir.iterdir()):
            services_dir.rmdir()
    _, errors = inv.validate()
    assert errors == []


def test_n01_unowned_second_authoritative_store_is_rejected(tmp_path):
    registry = json.loads(inv.REGISTRY_PATH.read_text())
    entries = registry["entries"]
    # Two present entries claiming the same authoritative state class with
    # different owners must be rejected as duplicate authority.
    for entry in entries:
        if entry.get("state_class") == "relational_primary":
            entry["status"] = "present"
            clone = dict(entry)
            clone["owner"] = "quansio-runtime"
            clone["path"] = "deploy/compose/second.yml#postgres"
            entries.append(clone)
            break
    else:
        raise AssertionError("registry fixture lacks relational_primary entry")
    (tmp_path / "deploy").mkdir()
    resolved, errors = inv.validate(root=tmp_path, registry=registry)
    assert any("duplicate authoritative state class relational_primary" in e for e in errors), errors


def test_r01_tracked_input_change_is_detected_then_recovery_is_clean():
    committed = inv.INVENTORY_PATH.read_text()
    original_registry = inv.REGISTRY_PATH.read_bytes()
    try:
        registry = json.loads(original_registry)
        target = next(e for e in registry["entries"] if e["path"] == "tools")
        target["owner"] = "authority"
        inv.REGISTRY_PATH.write_text(json.dumps(registry, indent=2) + "\n")
        resolved, errors = inv.validate()
        drifted = inv.render(inv.build_inventory(resolved))
        assert drifted != committed, "ownership input change did not produce detectable drift"
    finally:
        inv.REGISTRY_PATH.write_bytes(original_registry)
    resolved, errors = inv.validate()
    assert errors == []
    assert inv.render(inv.build_inventory(resolved)) == committed, "regeneration did not return to clean state"


def test_r01_planned_path_adopted_only_through_registry():
    probe_file = REPO_ROOT / "services" / "quansio_notify" / "main.py"
    probe_file.parent.mkdir(parents=True, exist_ok=True)
    probe_file.write_text("entrypoint probe\n")
    try:
        _, errors = inv.validate()
        assert any("planned path now exists" in e
                   and "entrypoint:services/quansio_notify/main.py" in e for e in errors), errors
    finally:
        probe_file.unlink()
        if not any((REPO_ROOT / "services" / "quansio_notify").iterdir()):
            (REPO_ROOT / "services" / "quansio_notify").rmdir()
    _, errors = inv.validate()
    assert errors == []
