"""Canonical contract binding for RecoveryConsistencyPoint.

Generated from schemas/RecoveryConsistencyPoint.schema.json digest 60d7b9f10aa0da84ed3f1d0602780272e16da26bccdb8c40e4e7363ae5789a2d by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "60d7b9f10aa0da84ed3f1d0602780272e16da26bccdb8c40e4e7363ae5789a2d"
SCHEMA = json.loads("""{"$id":"quansio://schema/RecoveryConsistencyPoint/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"created_at":{"format":"date-time","type":"string"},"database_position":{"minLength":1,"type":"string"},"effect_settlement_watermark":{"minLength":1,"type":"string"},"evidence_manifest_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"recovery_point_id":{"minLength":1,"type":"string"},"runtime_event_sequence":{"minimum":0,"type":"integer"},"schema_revision":{"const":"9.0.0"},"snapshot_inventory_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"unresolved_unknown_effect_ids":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true}},"required":["schema_revision","recovery_point_id","database_position","runtime_event_sequence","evidence_manifest_digest","snapshot_inventory_digest","effect_settlement_watermark","unresolved_unknown_effect_ids","created_at"],"title":"RecoveryConsistencyPoint","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class RecoveryConsistencyPoint:
    created_at: str
    database_position: str
    effect_settlement_watermark: str
    evidence_manifest_digest: str
    recovery_point_id: str
    runtime_event_sequence: int
    schema_revision: Any
    snapshot_inventory_digest: str
    unresolved_unknown_effect_ids: list

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('created_at', 'database_position', 'effect_settlement_watermark', 'evidence_manifest_digest', 'recovery_point_id', 'runtime_event_sequence', 'schema_revision', 'snapshot_inventory_digest', 'unresolved_unknown_effect_ids',)})
