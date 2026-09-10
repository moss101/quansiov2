"""GOV-003 acceptance tests: canonical schema and generated-binding gate.

Positive: every registered schema generates bindings and validates its
fixtures; generation is deterministic with no hand-written competing DTO.
Negative: a hand-written shadow DTO named like a canonical schema is
rejected. Recovery: after a schema edit, the freshness check rejects stale
bindings and regeneration restores a fully fresh state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools/governance"))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

import contract_gate  # noqa: E402
import generate_bindings  # noqa: E402
import quansio_contracts  # noqa: E402


def test_p03_every_schema_has_fresh_binding_and_valid_fixtures():
    outputs = generate_bindings.build_outputs()
    schemas = generate_bindings.load_schemas()
    assert len(schemas) == 43
    for name, schema, _digest in schemas:
        snake = generate_bindings.snake(name)
        assert f"generated/contracts/python/quansio_contracts/{snake}.py" in outputs
        assert f"generated/contracts/typescript/{name}.ts" in outputs
    stale = [
        rel
        for rel, text in outputs.items()
        if not (REPO_ROOT / rel).is_file() or (REPO_ROOT / rel).read_text() != text
    ]
    assert stale == [], f"stale bindings: {stale[:5]}"
    valid_dir = REPO_ROOT / "tests/fixtures/valid"
    for path in sorted(valid_dir.glob("*.json")):
        binding = getattr(quansio_contracts, path.stem)
        binding.validate(json.loads(path.read_text()))


def test_p03_generation_is_deterministic():
    first = generate_bindings.build_outputs()
    second = generate_bindings.build_outputs()
    assert first == second


def test_p03_no_competing_dtos_in_production_tree():
    assert contract_gate.find_shadow_dtos() == []


def test_n03_shadow_dto_is_rejected(tmp_path):
    production = tmp_path / "quansio"
    production.mkdir()
    (production / "shadow_probe.py").write_text(
        "class CommandEnvelope:\n    command_id: str\n"
    )
    shadows = contract_gate.find_shadow_dtos(roots=[production])
    assert any(name == "CommandEnvelope" and rel.endswith("shadow_probe.py") for rel, _, name in shadows)


def test_n03_live_repo_rejects_shadow_dto():
    probe = REPO_ROOT / "quansio" / "shadow_probe.py"
    probe.parent.mkdir(parents=True, exist_ok=True)
    try:
        probe.write_text("class ApprovalRequest:\n    approval_id: str\n")
        shadows = contract_gate.find_shadow_dtos()
        assert any(rel == "quansio/shadow_probe.py" for rel, _, _ in shadows)
    finally:
        probe.unlink()
        if not any((REPO_ROOT / "quansio").iterdir()):
            (REPO_ROOT / "quansio").rmdir()
    assert contract_gate.find_shadow_dtos() == []


def test_r03_schema_edit_makes_bindings_stale_then_regeneration_restores():
    schema_path = REPO_ROOT / "schemas" / "ToolOperation.schema.json"
    original = schema_path.read_bytes()
    bindings_path = REPO_ROOT / "generated/contracts/python/quansio_contracts/tool_operation.py"
    try:
        schema = json.loads(original)
        schema["properties"]["governance_probe"] = {"type": "string"}
        schema_path.write_text(json.dumps(schema, indent=2) + "\n")
        outputs = generate_bindings.build_outputs()
        on_disk = bindings_path.read_text()
        assert outputs[f"generated/contracts/python/quansio_contracts/tool_operation.py"] != on_disk, (
            "schema edit did not invalidate the generated binding"
        )
        import subprocess

        subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools/governance/generate_bindings.py"), "--write"],
            check=True,
            capture_output=True,
        )
        fresh = generate_bindings.build_outputs()
        assert fresh[f"generated/contracts/python/quansio_contracts/tool_operation.py"] == bindings_path.read_text()
    finally:
        schema_path.write_bytes(original)
        import subprocess

        subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools/governance/generate_bindings.py"), "--write"],
            check=True,
            capture_output=True,
        )
    outputs = generate_bindings.build_outputs()
    assert outputs[f"generated/contracts/python/quansio_contracts/tool_operation.py"] == bindings_path.read_text()
