"""Provider-neutral adapter contract (MOD-002).

An adapter translates one provider profile's wire protocol into canonical
``ModelEvent`` streams. Provider-specific fields never leave the adapter
boundary: the gateway and runtime see only canonical events. A provider
payload missing mandatory identity/usage fields produces a typed
``ProviderProtocolFailure`` — the adapter never fabricates values.
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import threading
from typing import Any, Iterator

import httpx

from quansio.model_gateway.credentials import ProviderCredentials
from quansio_contracts import ModelEvent as ModelEventContract


class ProviderProtocolFailure(Exception):
    """The provider payload violated the protocol contract; nothing fabricated."""

    def __init__(self, profile_id: str, reason: str):
        super().__init__(f"[{profile_id}] {reason}")
        self.profile_id = profile_id
        self.reason = reason


class ProviderUnreachable(Exception):
    def __init__(self, profile_id: str, reason: str):
        super().__init__(f"[{profile_id}] {reason}")
        self.profile_id = profile_id
        self.reason = reason


@dataclass(frozen=True)
class CanonicalRequest:
    request_id: str
    model_profile_id: str
    messages: list[dict]
    sampling: dict
    trace_id: str


class ProviderAdapter(ABC):
    """One adapter instance per enabled provider profile."""

    protocol: str

    def __init__(self, credentials: ProviderCredentials):
        self._credentials = credentials

    @property
    def profile_id(self) -> str:
        return self._credentials.profile_id

    @abstractmethod
    def stream(self, request: CanonicalRequest, outbound_capture: list[bytes] | None = None,
               cancel_event: threading.Event | None = None) -> Iterator[ModelEventContract]:
        """Yield canonical ModelEvents; optionally capture exact outbound bytes
        for privacy verification. A set ``cancel_event`` unwinds provider
        streaming at the next chunk boundary."""

    @abstractmethod
    def probe(self) -> bool:
        """Fresh health probe used for outage re-entry (MOD-007)."""


def _event(request: CanonicalRequest, sequence: int, event_type: str, payload: dict) -> ModelEventContract:
    return ModelEventContract.from_dict(
        {
            "schema_revision": "9.0.0",
            "event_id": str(uuid.uuid4()),
            "request_id": request.request_id,
            "run_id": "gateway-stream",  # enriched by the gateway before delivery
            "step_id": "gateway-stream",
            "execution_generation": 1,
            "model_profile_id": request.model_profile_id,
            "route_decision_id": "adapter",
            "sequence": sequence,
            "event_type": event_type,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
    )


class OpenAICompatibleAdapter(ProviderAdapter):
    """Adapter for OpenAI-compatible chat providers (llama.cpp, vLLM, OpenAI)."""

    protocol = "openai-chat"

    def stream(self, request: CanonicalRequest, outbound_capture: list[bytes] | None = None,
               cancel_event: threading.Event | None = None) -> Iterator[ModelEventContract]:
        body = {
            "model": self._credentials.profile_id,
            "messages": request.messages,
            "stream": True,
            "stream_options": {"include_usage": True},
            **(request.sampling or {}),
        }
        content = json.dumps(body).encode()
        if outbound_capture is not None:
            outbound_capture.append(content)
        headers = {"Content-Type": "application/json"}
        if self._credentials.api_key:
            headers["Authorization"] = f"Bearer {self._credentials.api_key}"
        sequence = 0
        terminal_seen = False
        try:
            with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
                with client.stream(
                    "POST",
                    f"{self._credentials.base_url.rstrip('/')}/chat/completions",
                    content=content,
                    headers=headers,
                ) as response:
                    if response.status_code == 429:
                        raise ProviderUnreachable(self.profile_id, "rate limited (HTTP 429)")
                    if response.status_code >= 500:
                        raise ProviderUnreachable(self.profile_id, f"provider outage (HTTP {response.status_code})")
                    if response.status_code != 200:
                        raise ProviderProtocolFailure(self.profile_id, f"unexpected HTTP status {response.status_code}")
                    sequence += 1
                    yield _event(request, sequence, "MODEL_STARTED", {"protocol": self.protocol})
                    usage: dict | None = None
                    finish_reason: str | None = None
                    content_text: list[str] = []
                    for line in response.iter_lines():
                        if cancel_event is not None and cancel_event.is_set():
                            response.close()
                            return
                        if terminal_seen:
                            raise ProviderProtocolFailure(self.profile_id, "data after terminal chunk")
                        if not line.startswith("data:"):
                            continue
                        data = line[len("data:"):].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError as error:
                            raise ProviderProtocolFailure(self.profile_id, f"malformed SSE chunk: {error}") from error
                        choices = chunk.get("choices")
                        if chunk.get("usage") is not None:
                            usage = self._mandatory_usage(self.profile_id, chunk["usage"])
                        if not isinstance(choices, list):
                            raise ProviderProtocolFailure(self.profile_id, "chunk missing choices")
                        if len(choices) > 1:
                            raise ProviderProtocolFailure(self.profile_id, "chunk carries multiple choices")
                        if not choices:
                            # Usage-only terminal chunk (stream_options.include_usage).
                            continue
                        choice = choices[0]
                        delta = choice.get("delta") or {}
                        text = delta.get("content")
                        if choice.get("finish_reason"):
                            finish_reason = choice["finish_reason"]
                        if text:
                            content_text.append(text)
                            sequence += 1
                            yield _event(request, sequence, "OUTPUT_DELTA", {"text": text})
                    if usage is None:
                        raise ProviderProtocolFailure(self.profile_id, "stream ended without mandatory usage")
                    if finish_reason is None:
                        raise ProviderProtocolFailure(self.profile_id, "stream ended without finish_reason")
                    sequence += 1
                    yield _event(
                        request,
                        sequence,
                        "MODEL_COMPLETED",
                        {
                            "usage": usage,
                            "finish_reason": finish_reason,
                            "output_text": "".join(content_text),
                            "terminal": True,
                        },
                    )
                    terminal_seen = True
        except httpx.ConnectError as error:
            raise ProviderUnreachable(self.profile_id, f"connection failed: {error}") from error
        except httpx.ReadTimeout as error:
            raise ProviderUnreachable(self.profile_id, f"timeout: {error}") from error

    def probe(self) -> bool:
        """Fresh health probe against the provider's HTTP surface."""
        try:
            with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
                response = client.get(f"{self._credentials.base_url.rstrip('/')}/health")
                if response.status_code == 200:
                    return True
                response = client.get(f"{self._credentials.base_url.rstrip('/')}/models")
                return response.status_code == 200
        except Exception:  # noqa: BLE001 - probe failures are health signal
            return False

    @staticmethod
    def _mandatory_usage(profile_id: str, usage: Any) -> dict:
        if not isinstance(usage, dict):
            raise ProviderProtocolFailure(profile_id, "usage is not an object")
        out = {}
        for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = usage.get(field)
            if not isinstance(value, int) or value < 0:
                raise ProviderProtocolFailure(profile_id, f"usage field {field} missing or invalid: {value!r}")
            out[field] = value
        return out


def adapter_for(credentials: ProviderCredentials) -> ProviderAdapter:
    if credentials.protocol == "openai-chat":
        return OpenAICompatibleAdapter(credentials)
    raise ProviderProtocolFailure(credentials.profile_id, f"unknown protocol {credentials.protocol}")
