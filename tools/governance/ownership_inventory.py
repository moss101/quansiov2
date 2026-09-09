"""Canonical ownership inventory for the Quansio repository.

Deterministically discovers production entrypoints, durable stores, service
packages, authority, governance, test, evidence, client and deploy paths and
verifies every discovered path is registered to exactly one canonical owner
or explicit disposition in ``evidence/ownership/ownership_registry.json``.

The registry is the tracked ownership input; this module is the deterministic
discovery ruleset. ``--check`` fails on: unowned discovered paths, stale
registry entries the ruleset cannot see, planned paths that now exist without
adoption, duplicate authoritative state ownership, and any drift between the
committed inventory file and the regenerated inventory.

Usage::

    python tools/governance/ownership_inventory.py           # validate + check drift
    python tools/governance/ownership_inventory.py --write   # regenerate inventory
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import RULESET_VERSION, iter_payload_files, sha256_bytes, sha256_file  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "evidence/ownership/ownership_registry.json"
INVENTORY_PATH = ROOT / "evidence/ownership/inventory.json"
INVENTORY_VERSION = "1.0.0"

KINDS = {
    "entrypoint",
    "durable_store",
    "package_path",
    "authority_path",
    "governance_path",
    "test_path",
    "evidence_path",
    "client_path",
    "deploy_path",
    "generated_path",
}

AUTHORITY_DIRS = {"docs", "graphs", "prompts", "protocols", "registries", "schemas", "scripts", "wiring"}
ROOT_DIR_KINDS = {
    "tools": "governance_path",
    "tests": "test_path",
    "evidence": "evidence_path",
    "deploy": "deploy_path",
    "services": "deploy_path",
    "clients": "client_path",
    "generated": "generated_path",
    "migrations": "durable_store",
    "quansio": "package_path",
}

ENTRYPOINT_FILENAMES = {"main.py", "asgi.py", "cli.py"}
STORE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _parse_project_scripts(path: Path) -> list[str]:
    """Extract [project.scripts] entry names deterministically (no toml dep)."""
    try:
        text = path.read_text()
    except OSError:
        return []
    names = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_section = stripped == "[project.scripts]"
            continue
        if not in_section or not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^([\w.-]+)\s*=\s*[\"']([\w.:]+)[\"']\s*$", stripped)
        if match:
            names.append(match.group(1))
    return sorted(names)


def _parse_compose_services(path: Path) -> list[str]:
    import yaml  # lazy: only needed once compose topology exists

    try:
        document = yaml.safe_load(path.read_text())
    except OSError:
        return []
    if not isinstance(document, dict):
        return []
    services = document.get("services")
    if not isinstance(services, dict):
        return []
    return sorted(services)


def discover(root: Path = ROOT) -> list[dict]:
    """Return sorted deterministic discovery candidates: {kind, path, detail}."""
    root = Path(root)
    found: dict[tuple[str, str], str] = {}
    claimed_root_names: set[str] = set()

    def add(kind: str, path: str, detail: str = "") -> None:
        key = (kind, path)
        if key in found and found[key] != detail:
            raise SystemExit(f"discovery conflict for {kind}:{path}")
        found[key] = detail
        if "#" not in path and "/" not in path:
            claimed_root_names.add(path)
        elif "#" not in path:
            claimed_root_names.add(path.split("/")[0])

    payload_files = list(iter_payload_files(root))
    rel_paths = {_rel(root, p): p for p in payload_files}

    # Root-level files are individually owned authority payload.
    for rel, path in sorted(rel_paths.items()):
        if "/" not in rel:
            add("authority_path", rel)

    # Root-level directories: known kinds plus unknown-dir fallback.
    root_dirs = sorted({rel.split("/")[0] for rel in rel_paths if "/" in rel})
    for name in root_dirs:
        if name in AUTHORITY_DIRS:
            add("authority_path", name)
        elif name in ROOT_DIR_KINDS:
            add(ROOT_DIR_KINDS[name], name)
        else:
            add("authority_path", name)

    for rel, path in sorted(rel_paths.items()):
        parts = rel.split("/")
        name = parts[-1]
        # Production entrypoint modules anywhere in the payload.
        if name == "__main__.py":
            add("entrypoint", rel)
        # Deployable entrypoints under services/.
        if len(parts) == 3 and parts[0] == "services" and name in ENTRYPOINT_FILENAMES:
            add("entrypoint", rel)
        # SQL migrations.
        if len(parts) >= 2 and parts[0] == "migrations" and path.suffix == ".sql":
            add("durable_store", rel)
        # Local database files are durable stores by definition.
        if path.suffix in STORE_SUFFIXES:
            add("durable_store", rel)
        # Deployment entrypoints.
        if len(parts) >= 2 and parts[0] == "deploy":
            if name.startswith("Dockerfile"):
                add("entrypoint", rel)
            if name.startswith("docker-compose") and path.suffix in {".yml", ".yaml"}:
                add("entrypoint", rel)
                for service in _parse_compose_services(path):
                    add("durable_store", f"{rel}#{service}")
        # Python packages per canonical owner module.
        if len(parts) == 2 and parts[0] == "quansio" and path.is_dir() and not name.startswith("_"):
            add("package_path", rel)
        # Client application packages.
        if len(parts) == 2 and parts[0] == "clients" and path.is_dir():
            add("client_path", rel)

    if (root / "pyproject.toml").is_file():
        for script in _parse_project_scripts(root / "pyproject.toml"):
            add("entrypoint", f"project.script:{script}")

    return [
        {"kind": kind, "path": path, "detail": detail}
        for (kind, path), detail in sorted(found.items())
    ]


def _entry_exists(root: Path, entry: dict) -> bool:
    path = entry["path"]
    if "#" in path:
        file_part, service = path.split("#", 1)
        file_path = root / file_part
        if not file_path.is_file():
            return False
        return service in _parse_compose_services(file_path)
    return (root / path).exists()


def validate(
    root: Path = ROOT, registry_path: Path = REGISTRY_PATH, registry: dict | None = None
) -> tuple[list[dict], list[str]]:
    """Validate registry against discovery; return (resolved_entries, errors)."""
    if registry is None:
        registry = json.loads(registry_path.read_text())
    errors: list[str] = []

    known_owners = set(registry["canonical_services"]) | set(registry["supporting_owners"])
    known_kinds = KINDS
    registered: dict[tuple[str, str], dict] = {}
    for entry in registry["entries"]:
        key = (entry["kind"], entry["path"])
        if key in registered:
            errors.append(f"duplicate registry entry {entry['kind']}:{entry['path']}")
        registered[key] = entry
        if entry["kind"] not in known_kinds:
            errors.append(f"unknown kind {entry['kind']} on {entry['path']}")
        if entry["owner"] not in known_owners:
            errors.append(f"unknown owner {entry['owner']} on {entry['path']}")
        if entry["status"] not in {"present", "planned"}:
            errors.append(f"unknown status {entry['status']} on {entry['path']}")

    state_owners: dict[str, str] = {}
    for entry in sorted(registry["entries"], key=lambda e: (e["kind"], e["path"])):
        path = entry["path"]
        exists = _entry_exists(root, entry)
        if entry["status"] == "present" and not exists:
            errors.append(f"registry entry marked present but path missing: {entry['kind']}:{path}")
        if entry["status"] == "planned" and exists:
            errors.append(f"planned path now exists; adopt it as present with its owner: {entry['kind']}:{path}")
        state_class = entry.get("state_class")
        if entry["status"] == "present" and state_class:
            if state_class != "non_authoritative_coordination":
                previous = state_owners.get(state_class)
                if previous and previous != entry["owner"]:
                    errors.append(
                        f"duplicate authoritative state class {state_class}: {previous} vs {entry['owner']} on {path}"
                    )
                state_owners[state_class] = entry["owner"]

    discovered = discover(root)
    resolved = []
    for candidate in discovered:
        key = (candidate["kind"], candidate["path"])
        entry = registered.get(key)
        if entry is None:
            errors.append(f"UNOWNED PATH: no registry entry for {candidate['kind']}:{candidate['path']}")
            continue
        resolved.append({k: entry[k] for k in ("kind", "path", "owner", "status", "state_class", "role")})

    discovered_keys = {(c["kind"], c["path"]) for c in discovered}
    for (kind, path), entry in sorted(registered.items()):
        if entry["status"] == "present" and (kind, path) not in discovered_keys:
            errors.append(f"STALE REGISTRY: present entry not discovered by ruleset: {kind}:{path}")

    resolved.sort(key=lambda e: (e["kind"], e["path"]))
    return resolved, errors


def build_inventory(resolved_entries: list[dict], registry_path: Path = REGISTRY_PATH) -> dict:
    return {
        "inventory_version": INVENTORY_VERSION,
        "ruleset_version": RULESET_VERSION,
        "registry_version": json.loads(registry_path.read_text())["registry_version"],
        "registry_sha256": sha256_file(registry_path),
        "tooling_sha256": sha256_bytes(
            (Path(__file__).resolve().read_bytes() + (Path(__file__).resolve().parent / "repo_paths.py").read_bytes())
        ),
        "entry_count": len(resolved_entries),
        "entries": resolved_entries,
    }


def render(inventory: dict) -> str:
    return json.dumps(inventory, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate the committed inventory file")
    parser.add_argument("--check", action="store_true", help="explicit drift check (default behaviour)")
    args = parser.parse_args()

    resolved, errors = validate(ROOT)
    inventory = build_inventory(resolved)
    rendered = render(inventory)

    if errors:
        print("OWNERSHIP INVENTORY: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    if args.write:
        INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        INVENTORY_PATH.write_text(rendered)
        print(f"OWNERSHIP INVENTORY: WRITTEN ({inventory['entry_count']} entries)")
        return 0

    if not INVENTORY_PATH.is_file():
        print("OWNERSHIP INVENTORY: FAIL (inventory file missing; run with --write)")
        return 1
    if INVENTORY_PATH.read_text() != rendered:
        print("OWNERSHIP INVENTORY: FAIL (drift between committed inventory and regenerated inventory)")
        return 1
    print(f"OWNERSHIP INVENTORY: PASS ({inventory['entry_count']} owned entries, no unowned paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
