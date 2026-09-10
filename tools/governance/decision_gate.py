"""Decision-record and threat-model workflow gate (GOV-007).

Enforces the doc-35 decision record contract:

- every ``docs/decisions/*.md`` record carries all template fields with a
  valid Status (PROPOSED|ACCEPTED|REJECTED|RETIRED);
- referenced task IDs exist in ``registries/tasks.json`` and referenced
  schema files exist (no orphaned references);
- canonical services citing a decision (ownership registry ``decision_id``)
  cite an ACCEPTED record — changing a canonical owner, effect class or
  security invariant without an accepted decision fails this gate.

Usage::

    python tools/governance/decision_gate.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISIONS_DIR = ROOT / "docs/decisions"
REGISTRY_PATH = ROOT / "evidence/ownership/ownership_registry.json"

REQUIRED_FIELDS = [
    "Decision ID:",
    "Owner:",
    "Status:",
    "Context:",
    "Problem:",
    "Decision:",
    "Alternatives considered:",
    "Affected architectural invariants:",
    "Affected canonical owners/schemas/wiring:",
    "Threat/privacy/tenant impact:",
    "Data migration/compatibility impact:",
    "Rollback/reversal plan:",
    "Testing/qualification impact:",
    "Review trigger/date:",
]
VALID_STATUSES = {"PROPOSED", "ACCEPTED", "REJECTED", "RETIRED"}
TASK_ID_PATTERN = re.compile(r"\b([A-Z]{2,4}-\d{3})\b")
SCHEMA_REF_PATTERN = re.compile(r"\b([A-Za-z]+\.schema\.json)\b")


def parse_record(path: Path) -> tuple[dict[str, str], list[str]]:
    """Return ({field: value}, missing_fields) for a decision record."""
    text = path.read_text()
    fields: dict[str, str] = {}
    missing = []
    lines = text.splitlines()
    for index, field in enumerate(REQUIRED_FIELDS):
        found = None
        for line in lines:
            if line.startswith(field):
                found = line[len(field) :].strip()
                break
        if found is None:
            missing.append(field)
        else:
            fields[field] = found
    # Capture full multi-line values for fields we evaluate (Status, Decision ID).
    for field in ("Status:", "Decision ID:"):
        match = re.search(rf"^{re.escape(field)}\s*(.+)$", text, re.M)
        if match:
            fields[field] = match.group(1).splitlines()[0].strip()
    return fields, missing


def load_records() -> dict[str, dict]:
    """Return {decision_id: {id, status, path, text, fields}} for all records."""
    records = {}
    for path in sorted(DECISIONS_DIR.glob("*.md")):
        text = path.read_text()
        fields, _missing = parse_record(path)
        decision_id = fields.get("Decision ID:", "")
        status = fields.get("Status:", "").strip().upper().split()[0] if fields.get("Status:") else ""
        records[decision_id or path.stem] = {
            "id": decision_id,
            "status": status,
            "path": path,
            "text": text,
            "fields": fields,
        }
    return records


def validate() -> list[str]:
    errors: list[str] = []
    tasks = json.loads((ROOT / "registries/tasks.json").read_text())
    requirements = json.loads((ROOT / "registries/requirements.json").read_text())
    known_ids = {t["task_id"] for t in tasks} | {r["requirement_id"] for r in requirements}
    schema_files = {p.name for p in (ROOT / "schemas").glob("*.schema.json")}
    records = load_records()

    numeric_ids = set()
    for decision_id, record in records.items():
        if not decision_id.startswith("ADR-"):
            errors.append(f"{record['path'].name}: missing or malformed Decision ID")
            continue
        numeric_ids.add(decision_id)
        if record["status"] not in VALID_STATUSES:
            errors.append(f"{decision_id}: invalid Status {record['status']!r}")
        _fields, missing = parse_record(record["path"])
        if missing:
            errors.append(f"{decision_id}: missing template fields: {missing}")
        for ref_id in TASK_ID_PATTERN.findall(record["text"]):
            if ref_id not in known_ids:
                errors.append(f"{decision_id}: orphaned registry reference {ref_id}")
        for schema_ref in SCHEMA_REF_PATTERN.findall(record["text"]):
            if schema_ref not in schema_files:
                errors.append(f"{decision_id}: orphaned schema reference {schema_ref}")

    registry = json.loads(REGISTRY_PATH.read_text())
    for service, spec in registry["canonical_services"].items():
        decision_id = spec.get("decision_id")
        if not decision_id:
            errors.append(f"canonical service {service} lacks decision_id")
            continue
        record = records.get(decision_id)
        if record is None:
            errors.append(f"canonical service {service} cites unknown decision {decision_id}")
        elif record["status"] != "ACCEPTED":
            errors.append(
                f"canonical service {service} cites decision {decision_id} with status {record['status']}; accepted decision required"
            )
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("DECISION GATE: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"DECISION GATE: PASS ({len(load_records())} records, all registry citations accepted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
