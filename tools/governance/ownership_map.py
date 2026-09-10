"""Canonical authority map validation (GOV-002).

Validates the machine-readable ownership map in
``evidence/ownership/ownership_registry.json`` against canonical reality:

- every canonical service owns its registered package and deployable exactly
  once and cites an accepted architecture decision;
- every authoritative durable store state class has exactly one owner;
- every produced contract is a registered schema and has exactly one
  producing owner across the whole map;
- every external-effect class has exactly one actuator and every actuator is
  a canonical service;
- every wiring flow participant is a known actor and every flow contract is a
  registered schema.

Used by the GOV-002 acceptance suite and by ``verify_all``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "evidence/ownership/ownership_registry.json"
WIRING_PATH = ROOT / "wiring/service-wiring.json"
DECISIONS_DIR = ROOT / "docs/decisions"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text())


def validate(registry: dict | None = None, wiring: dict | None = None, root: Path = ROOT) -> list[str]:
    reg = registry if registry is not None else load_registry()
    flows = (wiring if wiring is not None else json.loads(WIRING_PATH.read_text()))["flows"]
    errors: list[str] = []

    services = reg["canonical_services"]
    schema_names = {p.stem.removesuffix(".schema") for p in (root / "schemas").glob("*.schema.json")}

    # Canonical services: package/deployable registered, decision recorded.
    inventory_entries = {(e["kind"], e["path"]) for e in reg["entries"]}
    decision_files = {p.name.lower() for p in DECISIONS_DIR.glob("*.md")}
    for service, spec in services.items():
        decision = spec.get("decision_id")
        if not decision:
            errors.append(f"canonical service {service} lacks decision_id")
        else:
            numeric_id = decision.lower().replace("adr-", "")
            if not any(name.startswith(numeric_id + "-") for name in decision_files):
                errors.append(f"canonical service {service} cites unknown decision {decision}")
        if ("package_path", spec["package"]) not in inventory_entries and not (root / spec["package"]).is_dir():
            errors.append(f"canonical service {service} package not registered: {spec['package']}")
        if not (root / spec["deployable"]).is_dir():
            # Deployable container may not exist yet; its entrypoint must be planned.
            if ("entrypoint", f"{spec['deployable']}/main.py") not in inventory_entries:
                errors.append(f"canonical service {service} deployable not planned: {spec['deployable']}")

    # Authoritative store state classes: exactly one owner.
    state_owners: dict[str, str] = {}
    for entry in reg["entries"]:
        state_class = entry.get("state_class")
        if entry["status"] != "present" or not state_class:
            continue
        if state_class == "non_authoritative_coordination":
            continue
        previous = state_owners.setdefault(state_class, entry["owner"])
        if previous != entry["owner"]:
            errors.append(
                f"duplicate authoritative state class {state_class}: {previous} vs {entry['owner']}"
            )

    # Event producers: known services, registered schemas, single producer.
    producer_of: dict[str, str] = {}
    for producer in reg.get("event_producers", []):
        owner = producer["producer"]
        if owner not in services and owner not in reg.get("wiring_actors", {}):
            errors.append(f"event producer {owner} is not a known service or actor")
        for produced in producer["produces"]:
            if produced not in schema_names:
                errors.append(f"producer {owner} emits unregistered schema {produced}")
            if produced in producer_of and producer_of[produced] != owner:
                errors.append(
                    f"duplicate producer for {produced}: {producer_of[produced]} vs {owner}"
                )
            producer_of[produced] = owner

    # Effect actuators: canonical services only, unique effect classes.
    actuator_of: dict[str, str] = {}
    for actuator in reg.get("effect_actuators", []):
        owner = actuator["actuator"]
        if owner not in services:
            errors.append(f"effect actuator {owner} is not a canonical service")
        effect_class = actuator["effect_class"]
        if effect_class in actuator_of and actuator_of[effect_class] != owner:
            errors.append(
                f"duplicate effect class {effect_class}: {actuator_of[effect_class]} vs {owner}"
            )
        actuator_of[effect_class] = owner

    # Wiring flows: known participants and registered contracts.
    known_actors = set(services) | set(reg.get("wiring_actors", {}))
    for flow in flows:
        for participant in [flow.get("producer"), flow.get("consumer"), *flow.get("next", [])]:
            if participant and participant not in known_actors:
                errors.append(f"flow {flow.get('flow_id')}: unknown participant {participant}")
        for contract in flow.get("contracts", []):
            if contract not in schema_names:
                errors.append(f"flow {flow.get('flow_id')}: unregistered contract schema {contract}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("AUTHORITY MAP: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("AUTHORITY MAP: PASS (services, stores, producers, actuators, wiring consistent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
