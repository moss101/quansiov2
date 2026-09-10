"""Canonical streaming with validation, cancellation and backpressure (MOD-004).

The canonical stream contract: MODEL_STARTED first (sequence 1), strictly
increasing sequences, exactly one terminal event (MODEL_COMPLETED,
MODEL_CANCELLED or MODEL_FAILED) last. The validator rejects or normalizes
invalid conditions before they reach the runtime. Consumption uses a bounded
queue: a slow consumer blocks the producer (backpressure), and cancellation
during blocked consumption unwinds provider streaming, emits the terminal
MODEL_CANCELLED and settles the usage reservation.
"""

from __future__ import annotations

import queue
import threading
from typing import Iterator

from quansio.model_gateway.adapters import ProviderProtocolFailure
from quansio_contracts import ModelEvent as ModelEventContract

TERMINAL_TYPES = {"MODEL_COMPLETED", "MODEL_CANCELLED", "MODEL_FAILED"}


class InvalidStream(Exception):
    """A canonical-stream violation that must not reach the runtime."""


class StreamValidator:
    """Stateful validator for one canonical event stream."""

    def __init__(self):
        self._sequence = 0
        self._started = False
        self._terminal: str | None = None

    @property
    def terminal_seen(self) -> bool:
        return self._terminal is not None

    def accept(self, event: ModelEventContract) -> ModelEventContract:
        event_type = event.event_type
        if self._terminal is not None:
            raise InvalidStream(f"event after terminal {self._terminal}: {event_type}")
        if not self._started and event_type != "MODEL_STARTED":
            raise InvalidStream(f"pre-start event {event_type}")
        if event_type == "MODEL_STARTED":
            if self._started:
                raise InvalidStream("duplicate MODEL_STARTED")
            if event.sequence != 1:
                raise InvalidStream("MODEL_STARTED must carry sequence 1")
            self._started = True
        else:
            if event.sequence != self._sequence + 1:
                raise InvalidStream(
                    f"duplicate/non-monotonic sequence {event.sequence} (expected {self._sequence + 1})"
                )
        if event_type in TERMINAL_TYPES:
            self._terminal = event_type
        self._sequence = event.sequence
        return event


class BoundedEventChannel:
    """Bounded queue between adapter thread and consumer (backpressure)."""

    def __init__(self, maxsize: int = 4):
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._closed = False
        self._cancel_requested = threading.Event()

    def put(self, event: ModelEventContract, timeout: float | None = None) -> bool:
        """Producer side; blocks while the consumer is slow (backpressure).
        Returns False when the channel was cancelled/closed."""
        while not self._cancel_requested.is_set() and not self._closed:
            try:
                self._queue.put(event, timeout=timeout or 0.2)
                return True
            except queue.Full:
                continue
        return False

    def get(self, timeout: float | None = None) -> ModelEventContract | None:
        """Consumer side; returns None when the producer finished the stream."""
        try:
            item = self._queue.get(timeout=timeout if timeout is not None else 0.5)
        except queue.Empty:
            return None
        if item is _FINISHED:
            return None
        return item

    def put_error(self, error: Exception) -> None:
        """Deliver a producer-side failure to the consumer."""
        while not self._cancel_requested.is_set():
            try:
                self._queue.put(error, timeout=0.2)
                return
            except queue.Full:
                continue

    def cancel(self) -> None:
        self._cancel_requested.set()
        self._drain()

    def close(self) -> None:
        """Finish the stream: pending events stay queued ahead of the
        sentinel so a slow consumer still receives every event."""
        self._closed = True
        while True:
            try:
                self._queue.put(_FINISHED, timeout=5)
                return
            except queue.Full:
                if self._cancel_requested.is_set():
                    self._drain()
                    self._queue.put_nowait(_FINISHED)
                    return

    def _drain(self) -> None:
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass


_FINISH_SENTINEL = object()
_FINISHED = type("_Finished", (), {})()


def validated_stream(
    raw_events: Iterator[ModelEventContract],
) -> Iterator[ModelEventContract]:
    """Normalize an adapter stream through the canonical validator.

    Sequence violations and pre-start events are rejected here (dropped) so
    they never reach the runtime as valid events. Violations after a
    terminal event propagate: the gateway normalizes them into a typed
    MODEL_FAILED outcome.
    """
    validator = StreamValidator()
    for event in raw_events:
        try:
            yield validator.accept(event)
        except InvalidStream as violation:
            if validator.terminal_seen:
                raise
            continue
