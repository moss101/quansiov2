"""Shared repository traversal rules for authority tooling.

Single source of truth for which paths count as authority payload versus
VCS/derived state. Packaging (``scripts/finalize_package.py``), integrity
validation (``scripts/validate_integrity.py``) and the ownership inventory
(``tools/governance/ownership_inventory.py``) must enforce identical
coverage, so they all traverse through this module.

RULESET_VERSION changes whenever traversal semantics change; the ownership
inventory records it as a tracked input so drift is detectable.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

RULESET_VERSION = "1.0.0"

# Directory names that are never authority payload: VCS internals, language
# and toolchain caches, dependency trees, build outputs.
EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    ".tox",
    ".eggs",
    "node_modules",
    "dist",
    "build",
    ".quansio-venv",
}

# Repo-relative prefixes that are operational state rather than authority
# payload (provisioned environment manifests rotate on every provision; the
# committed real-boundary proof lives in evidence/boundary/ snapshots).
EXCLUDED_PREFIXES = {
    "evidence/environment/",
    # rotating qualification secrets (untracked operational state)
    "deploy/compose/.env.qual",
}

# Files never treated as payload by the inventory (integrity artifacts cover
# themselves cyclically or are reporting views).
INVENTORY_EXCLUDED_FILES = set()


def is_payload_dir(dirname: str) -> bool:
    return dirname not in EXCLUDED_DIR_NAMES


def iter_payload_files(root: Path):
    """Yield payload files under root in sorted deterministic order."""
    root = Path(root)
    stack = [root]
    while stack:
        current = stack.pop()
        for entry in sorted(current.iterdir(), key=lambda p: p.name):
            if entry.is_dir():
                if is_payload_dir(entry.name):
                    stack.append(entry)
            elif entry.is_file():
                rel = entry.relative_to(root).as_posix()
                if any(rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
                    continue
                yield entry


def payload_relative_paths(root: Path):
    """Sorted list of repo-relative POSIX paths for every payload file."""
    root = Path(root).resolve()
    return sorted(p.relative_to(root).as_posix() for p in iter_payload_files(root))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
