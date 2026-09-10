"""Canonical contract binding for BrowserSession.

Generated from schemas/BrowserSession.schema.json digest 9b72938131d1e3a877d7e3173d8f4422cfff1b5942b114d288f39e92388efd4c by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "9b72938131d1e3a877d7e3173d8f4422cfff1b5942b114d288f39e92388efd4c"
SCHEMA = json.loads("""{"$id":"quansio://schema/BrowserSession/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"browser_session_id":{"minLength":1,"type":"string"},"controller":{"enum":["AGENT","HUMAN","NONE"]},"created_at":{"format":"date-time","type":"string"},"current_url":{"type":["string","null"]},"execution_generation":{"minimum":1,"type":"integer"},"schema_revision":{"const":"9.0.0"},"state":{"enum":["STARTING","READY","TAKEOVER_PENDING","SUSPENDED","CLOSED","FAILED"]},"target_id":{"minLength":1,"type":"string"},"tenant_id":{"minLength":1,"type":"string"},"workspace_id":{"minLength":1,"type":"string"}},"required":["schema_revision","browser_session_id","tenant_id","workspace_id","target_id","execution_generation","controller","state","created_at"],"title":"BrowserSession","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class BrowserSession:
    browser_session_id: str
    controller: Any
    created_at: str
    execution_generation: int
    schema_revision: Any
    state: Any
    target_id: str
    tenant_id: str
    workspace_id: str
    current_url: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('browser_session_id', 'controller', 'created_at', 'current_url', 'execution_generation', 'schema_revision', 'state', 'target_id', 'tenant_id', 'workspace_id',)})
