"""Canonical contract binding for AgentGraph.

Generated from schemas/AgentGraph.schema.json digest 04b1a5611a5d334842f21b95cb6cfb3dc5dd99ce31f194da3d2373b15724d1ee by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "04b1a5611a5d334842f21b95cb6cfb3dc5dd99ce31f194da3d2373b15724d1ee"
SCHEMA = json.loads("""{"$id":"quansio://schema/AgentGraph/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"agentgraph_id":{"minLength":1,"type":"string"},"agents":{"items":{"additionalProperties":false,"properties":{"agent_id":{"minLength":1,"type":"string"},"capability_snapshot_id":{"minLength":1,"type":"string"},"lifecycle":{"enum":["PERSISTENT","EPHEMERAL"]},"owner_id":{"minLength":1,"type":"string"},"workspace_binding":{"type":["string","null"]}},"required":["agent_id","lifecycle","owner_id","capability_snapshot_id"],"type":"object"},"type":"array"},"schema_revision":{"const":"9.0.0"},"tenant_id":{"minLength":1,"type":"string"},"workspace_id":{"minLength":1,"type":"string"}},"required":["schema_revision","agentgraph_id","tenant_id","workspace_id","agents"],"title":"AgentGraph","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class AgentGraph:
    agentgraph_id: str
    agents: list
    schema_revision: Any
    tenant_id: str
    workspace_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('agentgraph_id', 'agents', 'schema_revision', 'tenant_id', 'workspace_id',)})
