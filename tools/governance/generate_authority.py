"""Deterministic authority generation (GOV-004).

Regenerates every derived canonical artifact from the canonical inputs
(``registries/tasks.json``, ``registries/requirements.json``,
``registries/support-matrix.json``):

- ``registries/task-graph.json`` (nodes + edges from depends_on);
- inverse requirement links (``task_ids`` in ``registries/requirements.json``);
- reading views (docs/19, docs/20, docs/34, master dossier);
- support mapping view (``generated/authority/support-mappings.md``);
- integrity metadata (manifest, checksums, seal via finalize_package.py).

Two consecutive generations are byte-identical. ``--check`` fails when any
derived artifact diverges from regeneration, which blocks hand-edited task
edges, milestone counts or stale views.

Usage::

    python tools/governance/generate_authority.py --check   # default
    python tools/governance/generate_authority.py --write
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import regenerate_authority_views  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GENERATOR_VERSION = "1.0.0"


def render_task_graph(tasks: list[dict]) -> str:
    graph = {
        "schema_revision": "9.0.0",
        "nodes": sorted(t["task_id"] for t in tasks),
        "edges": sorted(
            (
                {"from": dep, "to": t["task_id"]}
                for t in tasks
                for dep in t["depends_on"]
            ),
            key=lambda e: (e["from"], e["to"]),
        ),
    }
    return json.dumps(graph, indent=2, sort_keys=True) + "\n"


def render_support_mappings(supports: list[dict], suites: list[dict]) -> str:
    lines = [
        "# Support mappings",
        "",
        f"Generated from registries/support-matrix.json by tools/governance/generate_authority.py {GENERATOR_VERSION}. DO NOT EDIT.",
        "",
        "| Profile | Kind | Status | Required suites | Qualification tasks | Enabled when |",
        "|---|---|---|---|---|---|",
    ]
    for profile in sorted(supports, key=lambda p: p["profile_id"]):
        lines.append(
            f"| {profile['profile_id']} | {profile['kind']} | {profile['status']} "
            f"| {', '.join(sorted(profile['required_suites']))} "
            f"| {', '.join(sorted(profile['qualification_tasks']))} "
            f"| {profile['enabled_when']} |"
        )
    lines += ["", "## Qualification suites", ""]
    for suite in sorted(suites, key=lambda s: s["suite_id"]):
        tasks = ", ".join(sorted(suite.get("qualification_tasks", [])))
        description = suite.get("description") or suite.get("name") or ""
        lines.append(f"- `{suite['suite_id']}` — {description} tasks: {tasks}")
    return "\n".join(lines) + "\n"


def build_outputs() -> dict[str, str]:
    tasks = json.loads((ROOT / "registries/tasks.json").read_text())
    requirements = json.loads((ROOT / "registries/requirements.json").read_text())
    supports = json.loads((ROOT / "registries/support-matrix.json").read_text())
    suites = json.loads((ROOT / "registries/qualification-matrix.json").read_text())

    outputs: dict[str, str] = {}
    outputs["registries/task-graph.json"] = render_task_graph(tasks)
    outputs["generated/authority/support-mappings.md"] = render_support_mappings(supports, suites)

    linked = {}
    for requirement in requirements:
        linked[requirement["requirement_id"]] = sorted(
            t["task_id"] for t in tasks if requirement["requirement_id"] in t["requirement_ids"]
        )
    requirements_normalized = []
    for requirement in sorted(requirements, key=lambda r: r["requirement_id"]):
        entry = dict(requirement)
        entry["task_ids"] = linked[requirement["requirement_id"]]
        requirements_normalized.append(entry)
    outputs["registries/requirements.json"] = json.dumps(requirements_normalized, indent=2, sort_keys=True) + "\n"

    for rel, text in regenerate_authority_views.expected().items():
        outputs[rel] = text
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true", help="explicit drift check (default behaviour)")
    args = parser.parse_args()

    outputs = build_outputs()
    if args.write:
        for rel, text in sorted(outputs.items()):
            path = ROOT / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/finalize_package.py")], check=False
        )
        if result.returncode != 0:
            return result.returncode
        print(f"AUTHORITY GENERATION: WRITTEN ({len(outputs)} derived artifacts + integrity metadata)")
        return 0

    stale = [rel for rel, text in sorted(outputs.items()) if not (ROOT / rel).is_file() or (ROOT / rel).read_text() != text]
    if stale:
        print("AUTHORITY GENERATION: FAIL (stale or missing derived artifacts)")
        for rel in stale:
            print(f"- {rel}")
        return 1
    print(f"AUTHORITY GENERATION: PASS ({len(outputs)} derived artifacts byte-identical)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
