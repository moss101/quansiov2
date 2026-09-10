"""GOV-007 acceptance tests: decision and threat-model workflow.

Positive: decision records capture every template field and stay consistent
with registry truth. Negative: changing a canonical owner without an
accepted decision record is rejected by the ownership/decision gates.
Recovery: a reversible decision rollback (record retired, registry restored)
returns ownership and wiring validation to the prior accepted state with no
orphaned references.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools/governance"))

import decision_gate  # noqa: E402
import ownership_map  # noqa: E402


def test_p07_records_capture_all_template_fields():
    records = decision_gate.load_records()
    assert set(records) >= {"ADR-0001", "ADR-0002", "ADR-0003"}
    for decision_id, record in records.items():
        _fields, missing = decision_gate.parse_record(record["path"])
        assert missing == [], f"{decision_id} missing fields: {missing}"
        assert record["status"] in decision_gate.VALID_STATUSES


def test_p07_gate_passes_on_current_tree():
    assert decision_gate.validate() == []


def test_n07_owner_change_without_accepted_decision_is_blocked():
    registry = copy.deepcopy(ownership_map.load_registry())
    # Attempt to hand a second authoritative store to another owner citing a
    # decision that does not exist.
    registry["canonical_services"]["quansio-context"]["decision_id"] = "ADR-9999"
    errors = ownership_map.validate(registry=registry)
    assert any("cites unknown decision ADR-9999" in e and "quansio-context" in e for e in errors), errors

    # Same attempt citing a PROPOSED decision must also be blocked.
    registry["canonical_services"]["quansio-context"]["decision_id"] = "ADR-DRAFT"
    draft_record = {
        "id": "ADR-DRAFT",
        "status": "PROPOSED",
        "path": REPO_ROOT / "docs/decisions/0000-draft.md",
        "text": "Decision ID: ADR-DRAFT\nStatus: PROPOSED\n",
        "fields": {"Decision ID:": "ADR-DRAFT", "Status:": "PROPOSED"},
    }
    original_load = decision_gate.load_records
    decision_gate.load_records = lambda: {**original_load(), "ADR-DRAFT": draft_record}
    try:
        errors = ownership_map.validate(registry=registry)
    finally:
        decision_gate.load_records = original_load
    assert any("status PROPOSED" in e and "quansio-context" in e for e in errors), errors


def test_n07_orphaned_references_in_decision_are_rejected():
    records = decision_gate.load_records()
    fabricated = {
        "ADR-FAKE": {
            "id": "ADR-FAKE",
            "status": "ACCEPTED",
            "path": next(iter(records.values()))["path"],
            "text": "References orphaned task ZZZ-999 and schema Missing.schema.json",
            "fields": {},
        }
    }
    original_validate_body = decision_gate.load_records
    decision_gate.load_records = lambda: {**records, **fabricated}
    try:
        errors = decision_gate.validate()
    finally:
        decision_gate.load_records = original_validate_body
    assert any("ZZZ-999" in e for e in errors), errors
    assert any("Missing.schema.json" in e for e in errors), errors


def test_r07_decision_rollback_restores_accepted_state():
    registry = copy.deepcopy(ownership_map.load_registry())
    # Roll back ADR-0002 (mark RETIRED) while services still cite it.
    records = decision_gate.load_records()
    records["ADR-0002"]["status"] = "RETIRED"
    original_load = decision_gate.load_records
    decision_gate.load_records = lambda: records
    try:
        errors = ownership_map.validate(registry=registry)
        assert any("ADR-0002" in e and "RETIRED" in e for e in errors), errors
    finally:
        decision_gate.load_records = original_load
    # Restore: decision accepted again -> ownership and wiring valid, no orphans.
    assert ownership_map.validate(registry=registry) == []
    assert decision_gate.validate() == []
