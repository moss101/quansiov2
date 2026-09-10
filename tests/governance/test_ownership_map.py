"""GOV-002 acceptance tests: canonical authority map.

Positive: one machine-readable map covers services, stores, producers and
actuators without duplicate owners. Negative: assigning the same
authoritative state or effect to two owners fails naming both. Recovery:
removing a canonical owner invalidates dependent wiring; restoring it makes
the map valid again.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools/governance"))

import ownership_map  # noqa: E402


def test_p02_map_covers_services_stores_producers_actuators_without_duplicates():
    registry = ownership_map.load_registry()
    assert set(registry["canonical_services"]) == {
        "quansio-api",
        "quansio-control",
        "quansio-runtime",
        "quansio-model-gateway",
        "quansio-context",
        "quansio-indexer",
        "quansio-worker-gateway",
        "quansio-machine-control",
        "quansio-integration-broker",
        "quansio-artifact",
        "quansio-notify",
        "qworkerd",
    }
    assert registry["effect_actuators"], "no external-effect actuators mapped"
    assert registry["event_producers"], "no event producers mapped"
    assert ownership_map.validate() == []
    produced = [p for producer in registry["event_producers"] for p in producer["produces"]]
    assert len(produced) == len(set(produced)), "a contract has two producers in the committed map"


def test_n02_duplicate_authoritative_store_owner_is_rejected_with_both_identifiers():
    registry = copy.deepcopy(ownership_map.load_registry())
    for entry in registry["entries"]:
        if entry.get("state_class") == "artifact_object_store":
            entry["status"] = "present"
            clone = dict(entry)
            clone["path"] = "deploy/compose/other.yml#minio"
            clone["owner"] = "quansio-context"
            registry["entries"].append(clone)
            break
    errors = ownership_map.validate(registry=registry)
    assert any("artifact_object_store" in e and "quansio-artifact" in e and "quansio-context" in e for e in errors), errors


def test_n02_duplicate_effect_class_is_rejected_with_both_identifiers():
    registry = copy.deepcopy(ownership_map.load_registry())
    registry["effect_actuators"].append(
        {"actuator": "quansio-runtime", "effect_class": "guest_actuation", "description": "duplicate claim"}
    )
    errors = ownership_map.validate(registry=registry)
    assert any(
        "duplicate effect class guest_actuation" in e and "qworkerd" in e and "quansio-runtime" in e
        for e in errors
    ), errors


def test_n02_duplicate_event_producer_is_rejected_with_both_identifiers():
    registry = copy.deepcopy(ownership_map.load_registry())
    registry["event_producers"].append(
        {"producer": "quansio-api", "produces": ["RuntimeEvent"]}
    )
    errors = ownership_map.validate(registry=registry)
    assert any(
        "duplicate producer for RuntimeEvent" in e and "quansio-runtime" in e and "quansio-api" in e
        for e in errors
    ), errors


def test_r02_removing_canonical_owner_invalidates_wiring_then_restore_is_clean():
    registry = copy.deepcopy(ownership_map.load_registry())
    removed = registry["canonical_services"].pop("quansio-runtime")
    errors = ownership_map.validate(registry=registry)
    assert any("quansio-runtime" in e for e in errors), "removing runtime owner did not invalidate dependents"
    registry["canonical_services"]["quansio-runtime"] = removed
    assert ownership_map.validate(registry=registry) == []


def test_r02_unknown_wiring_participant_is_rejected():
    wiring = json.loads((REPO_ROOT / "wiring/service-wiring.json").read_text())
    mutated = copy.deepcopy(wiring)
    mutated["flows"][0]["consumer"] = "rogue-orchestrator"
    errors = ownership_map.validate(wiring=mutated)
    assert any("unknown participant rogue-orchestrator" in e for e in errors), errors
