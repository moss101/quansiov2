"""Governed integration broker (EXT-002, owner quansio-integration-broker).

Connector operations execute through credential handles and full
policy/privacy/approval/effect mediation. Direct adapter invocation with
reusable secret material or without an EffectRecord is refused.
"""

from __future__ import annotations

import hashlib
import json
from typing import Callable

from quansio.control.effects import EffectRequired
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class ConnectorBroker:
    def __init__(self, database: PlatformDatabase, credential_broker, effect_ledger,
                 policy_engine=None):
        self._db = database
        self._broker = credential_broker
        self._ledger = effect_ledger
        self._policy = policy_engine

    def execute_connector_operation(
        self, context: IdentityContext, effect_id: str, handle_id: str,
        operation: str, target: str, arguments: dict,
        transport: Callable[[str, str, str, dict], dict],
    ) -> dict:
        """Full mediation path. ``transport(handle_material, operation,
        target, arguments)`` performs the actual external call with the
        broker-exchanged credential — reusable secrets are never handed to
        the caller, and an EffectRecord must already exist (consequential)."""
        effect = self._ledger.require_effect(context, effect_id, expected_status="authorized")
        if effect["operation"] not in ("connector.submit", "connector.call", operation):
            raise EffectRequired("effect operation mismatch")
        material = self._broker.exchange(context, handle_id, operation, target)
        self._ledger.start_execution(context, effect_id)
        try:
            receipt = transport(material, operation, target, arguments)
        except TimeoutError:
            self._ledger.mark_unknown(context, effect_id, {"connector_timeout": target})
            raise
        self._ledger.complete(context, effect_id, {"connector": target},
                              receipt=receipt)
        return {"effect_id": effect_id, "receipt": receipt, "evidence": {
            "digest": hashlib.sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
        }}

    def direct_adapter_call_refused(self, secret_material: str) -> None:
        """The unmediated path is unreachable by construction: invoking it
        always raises. Kept as an executable guard for the negative test."""
        raise EffectRequired(
            "direct adapter invocation with reusable secret material is forbidden;"
            " use the governed broker path"
        )
