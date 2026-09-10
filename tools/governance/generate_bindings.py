"""Generate canonical contract bindings from registered schemas (GOV-003).

Reads every ``schemas/*.schema.json`` and deterministically renders:

- Python bindings: ``generated/contracts/python/<snake_name>.py`` with a
  frozen dataclass, the embedded schema and a ``jsonschema`` validator;
- TypeScript bindings: ``generated/contracts/typescript/<Name>.ts`` with the
  typed interface and the source schema digest.

Every generated file records the exact digest of the schema revision it was
generated from, so the contract gate can prove no stale binding survives a
schema edit. Hand-written competing DTOs are rejected by
``tools/governance/contract_gate.py``.

Usage::

    python tools/governance/generate_bindings.py            # check (exit 1 on drift)
    python tools/governance/generate_bindings.py --write    # regenerate
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
PY_OUT = ROOT / "generated/contracts/python"
TS_OUT = ROOT / "generated/contracts/typescript"
GENERATOR_VERSION = "1.0.0"

PY_TYPES = {"string": "str", "integer": "int", "number": "float", "boolean": "bool", "array": "list", "object": "dict"}
TS_TYPES = {"string": "string", "integer": "number", "number": "number", "boolean": "boolean", "array": "unknown[]", "object": "object"}


def sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def load_schemas() -> list[tuple[str, dict, str]]:
    schemas = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        raw = path.read_bytes()
        schema = json.loads(raw)
        schemas.append((schema["title"], schema, sha256_bytes(raw)))
    return schemas


def snake(name: str) -> str:
    out = "".join("_" + c.lower() if c.isupper() else c for c in name).lstrip("_")
    return out


def _type_names(prop: dict) -> list[str]:
    value = prop.get("type")
    if isinstance(value, list):
        return value
    return [value]


def py_type(prop: dict, optional: bool) -> str:
    names = _type_names(prop)
    parts = [PY_TYPES.get(name, "Any") for name in names]
    base = " | ".join(dict.fromkeys(parts))
    return f"{base} | None" if optional else base


def ts_type(prop: dict, optional: bool) -> str:
    names = _type_names(prop)
    parts = [TS_TYPES.get(name, "unknown") for name in names]
    base = " | ".join(dict.fromkeys(parts))
    return base + (" | undefined" if optional else "")


def render_python(name: str, schema: dict, digest: str) -> str:
    props: dict = schema.get("properties", {})
    required: list = schema.get("required", [])
    embedded = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    assert "'''" not in embedded
    lines = [
        f'"""Canonical contract binding for {name}.',
        "",
        f"Generated from schemas/{name}.schema.json digest {digest} by",
        f"tools/governance/generate_bindings.py {GENERATOR_VERSION}. DO NOT EDIT.",
        '"""',
        "from __future__ import annotations",
        "",
        "import json",
        "from dataclasses import dataclass",
        "from typing import Any",
        "",
        "import jsonschema",
        "",
        f'SCHEMA_DIGEST = "{digest}"',
        f'SCHEMA = json.loads("""{embedded}""")',
        "VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)",
        "",
        "",
        f"@dataclass(frozen=True)",
        f"class {name}:",
    ]
    if props:
        ordered = [k for k in props if k in required] + [k for k in props if k not in required]
        for prop_name in ordered:
            prop = props[prop_name]
            optional = prop_name not in required
            lines.append(f"    {prop_name}: {py_type(prop, optional)}" + (" = None" if optional else ""))
    else:
        lines.append("    payload: dict = None")
    lines += [
        "",
        "    @classmethod",
        "    def validate(cls, payload: dict) -> None:",
        "        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))",
        "        if errors:",
        '            raise ValueError("; ".join(e.message for e in errors))',
        "",
        "    @classmethod",
        "    def from_dict(cls, payload: dict) -> Any:",
        "        cls.validate(payload)",
    ]
    if props:
        keys = ", ".join(repr(k) for k in props)
        lines.append(f"        return cls(**{{k: payload.get(k) for k in ({keys},)}})")
    else:
        lines.append("        return cls(payload=payload)")
    lines.append("")
    return "\n".join(lines)


def render_typescript(name: str, schema: dict, digest: str) -> str:
    props: dict = schema.get("properties", {})
    required: list = schema.get("required", [])
    const = "".join(c.upper() if c.isupper() else "_" + c.upper() for c in name).lstrip("_")
    lines = [
        f"// Canonical contract binding for {name}.",
        f"// Generated from schemas/{name}.schema.json digest {digest} by",
        f"// tools/governance/generate_bindings.py {GENERATOR_VERSION}. DO NOT EDIT.",
        f"export const {const}_SCHEMA_DIGEST = '{digest}';",
        "",
        f"export interface {name} {{",
    ]
    for prop_name, prop in props.items():
        optional = prop_name not in required
        suffix = "?" if optional else ""
        lines.append(f"  {prop_name}{suffix}: {ts_type(prop, optional)};")
    lines += ["}", ""]
    return "\n".join(lines)


def build_outputs() -> dict[str, str]:
    outputs: dict[str, str] = {}
    schemas = load_schemas()
    py_exports = []
    ts_exports = []
    for name, schema, digest in schemas:
        outputs[f"generated/contracts/python/quansio_contracts/{snake(name)}.py"] = render_python(name, schema, digest)
        outputs[f"generated/contracts/typescript/{name}.ts"] = render_typescript(name, schema, digest)
        py_exports.append((snake(name), name))
        ts_exports.append(name)
    outputs["generated/contracts/python/quansio_contracts/__init__.py"] = (
        '"""Canonical contract bindings. Generated by tools/governance/generate_bindings.py. DO NOT EDIT."""\n'
        + "\n".join(f"from .{module} import {name}" for module, name in sorted(py_exports))
        + "\n\n__all__ = [\n"
        + "".join(f'    "{name}",\n' for _, name in sorted(py_exports, key=lambda x: x[1]))
        + "]\n"
    )
    outputs["generated/contracts/typescript/index.ts"] = (
        "// Canonical contract bindings. Generated by tools/governance/generate_bindings.py. DO NOT EDIT.\n"
        + "".join(f"export * from './{name}';\n" for name in sorted(ts_exports))
    )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    outputs = build_outputs()
    if args.write:
        for rel, text in sorted(outputs.items()):
            path = ROOT / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        print(f"BINDINGS: WRITTEN ({len(outputs)} files from {len(load_schemas())} schemas)")
        return 0

    stale = []
    for rel, text in sorted(outputs.items()):
        path = ROOT / rel
        if not path.is_file() or path.read_text() != text:
            stale.append(rel)
    if stale:
        print("BINDINGS: FAIL (stale or missing generated bindings)")
        for rel in stale:
            print(f"- {rel}")
        return 1
    print(f"BINDINGS: PASS ({len(outputs)} files fresh from {len(load_schemas())} schemas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
