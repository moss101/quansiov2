"""Non-authoritative lease/coordination cache (DAT-007, owner quansio-runtime).

Redis holds only leases, rate-limit counters and reconstruction-safe caches.
Flushing the cache must not lose canonical truth: leases and generations are
reacquired or invalidated from authoritative PostgreSQL state before any
execution resumes on them.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import redis

from quansio.platform.db import PlatformDatabase


@dataclass(frozen=True)
class Lease:
    resource: str
    holder: str
    generation: int
    ttl_seconds: int


class LeaseCache:
    """Lease coordination with generation fences validated against authoritative state."""

    def __init__(self, database: PlatformDatabase, redis_url: str, prefix: str = "quansio:lease"):
        self._db = database
        self._prefix = prefix
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def _key(self, resource: str) -> str:
        return f"{self._prefix}:{resource}"

    def acquire(self, resource: str, holder: str, ttl_seconds: int = 30) -> Lease | None:
        """Take over a resource lease; fenced by an authoritative generation."""
        generation = self._authoritative_generation(resource)
        token = str(uuid.uuid4())
        acquired = self._client.set(
            self._key(resource), f"{holder}:{generation}:{token}", ex=ttl_seconds, nx=True
        )
        if not acquired:
            return None
        return Lease(resource, holder, generation, ttl_seconds)

    def validate(self, lease: Lease) -> bool:
        """A cached lease is valid only if its generation still matches
        authoritative state and the cache entry is held by the holder."""
        raw = self._client.get(self._key(lease.resource))
        if raw is None:
            return False
        holder, generation, _token = raw.split(":", 2)
        return holder == lease.holder and int(generation) == self._authoritative_generation(lease.resource)

    def release(self, lease: Lease) -> None:
        raw = self._client.get(self._key(lease.resource))
        if raw and raw.split(":", 2)[0] == lease.holder:
            self._client.delete(self._key(lease.resource))

    def _authoritative_generation(self, resource: str) -> int:
        """Reconstruct the generation counter from authoritative state.

        The cache is never the source: on any cache loss the generation is
        recomputed from PostgreSQL so fences stay sound.
        """
        row = self._db.query_one(
            "SELECT COALESCE(MAX(generation), 0) FROM runs WHERE run_id = %s",
            (resource,),
        )
        return row[0] if row else 0

    def reacquire_or_invalidate(self, resource: str, holder: str, ttl_seconds: int = 30) -> Lease | None:
        """Post-restart recovery: drop any stale entry, then re-derive the
        lease strictly from authoritative state."""
        self._client.delete(self._key(resource))
        return self.acquire(resource, holder, ttl_seconds)

    def flush_all(self) -> None:
        self._client.flushall()
