"""Canonical contract gate (GOV-003).

Enforces that production code consumes only generated canonical bindings:

1. every registered schema validates its contract fixtures;
2. generated bindings are byte-fresh against the registered schema revision
   (no stale binding survives a schema edit);
3. no hand-written competing DTO exists: class/interface declarations named
   exactly like a canonical schema are rejected outside ``generated/``.

Usage::

    python tools/governance/contract_gate.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import iter_payload_files  # noqa: E402
import generate_bindings  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_ROOTS = ("quansio", "services", "tools", "clients")


def schema_titles() -> set[str]:
    return {title for title, _, _ in generate_bindings.load_schemas()}


def find_shadow_dtos(roots: list[Path] | None = None) -> list[tuple[str, int, str]]:
    shadows: list[tuple[str, int, str]] = []
    titles = schema_titles()
    if not titles:
        return shadows
    if roots is None:
        roots = [ROOT / name for name in PRODUCTION_ROOTS if (ROOT / name).is_dir()]
    pattern = re.compile(r"^\s*(?:export\s+)?(?:abstract\s+class|class|interface|type)\s+(" + "|".join(sorted(titles)) + r")\b")
    for base in roots:
        if not base.is_dir():
            continue
        for path in iter_payload_files(base):
            if path.suffix not in {".py", ".ts", ".tsx"}:
                continue
            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                match = pattern.match(line)
                if match:
                    try:
                        rel = path.relative_to(ROOT).as_posix()
                    except ValueError:
                        rel = str(path)
                    shadows.append((rel, lineno, match.group(1)))
    return shadows


def main() -> int:
    failures = False

    contracts = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_contracts.py")], text=True, capture_output=True
    )
    print(contracts.stdout.strip())
    if contracts.returncode != 0:
        print(contracts.stderr.strip())
        failures = True

    outputs = generate_bindings.build_outputs()
    stale = []
    for rel, text in sorted(outputs.items()):
        path = ROOT / rel
        if not path.is_file() or path.read_text() != text:
            stale.append(rel)
    if stale:
        failures = True
        print(f"CONTRACT GATE: {len(stale)} stale/missing generated bindings")
        for rel in stale:
            print(f"- {rel}")
    else:
        print(f"CONTRACT GATE: {len(outputs)} generated bindings fresh")

    shadows = find_shadow_dtos()
    if shadows:
        failures = True
        print(f"CONTRACT GATE: {len(shadows)} hand-written competing DTOs")
        for rel, lineno, name in shadows:
            print(f"- {rel}:{lineno}: class {name} competes with canonical schema binding")
    else:
        print("CONTRACT GATE: no hand-written competing DTOs")

    if failures:
        print("CONTRACT GATE: FAIL")
        return 1
    print("CONTRACT GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
