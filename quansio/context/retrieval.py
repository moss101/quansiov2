"""Retrieval adapters and source provenance (CTX-002).

Every retrieved candidate carries canonical source identity (normalized
URL), retrieval timestamp, freshness metadata, access status, a content
digest and a deduplication key. Candidates resolving to the same canonical
content are merged without losing distinct provenance. When a source
becomes inaccessible, its prior provenance is preserved as stale rather
than claimed fresh.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx


class SourceInaccessible(Exception):
    """The source could not be retrieved; prior provenance stays stale."""


def canonical_url(url: str) -> str:
    """Canonical source identity: lowercase host, no fragment, sorted query,
    no trailing slash ambiguity, tracking parameters removed."""
    parsed = urlparse(url.strip())
    query = [(k, v) for k, v in parse_qsl(parsed.query) if not k.startswith("utm_")]
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((
        parsed.scheme.lower() or "http",
        parsed.netloc.lower(),
        path,
        parsed.params,
        urlencode(sorted(query)),
        "",
    ))


def content_digest(content: str) -> str:
    normalized = re.sub(r"\s+", " ", content).strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


def dedup_key(url: str, content: str) -> str:
    return hashlib.sha256(f"{canonical_url(url)}|{content_digest(content)}".encode()).hexdigest()


@dataclass
class Candidate:
    url: str
    title: str
    content: str
    retrieved_at: str
    digest: str
    dedup_key: str
    source_id: str
    access_status: str = "accessible"
    freshness: str = "fresh"
    provenance: list[dict] = field(default_factory=list)

    def with_provenance(self, provenance: dict) -> "Candidate":
        self.provenance.append(provenance)
        return self


def merge_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Merge candidates with identical dedup keys, keeping every distinct
    provenance entry."""
    merged: dict[str, Candidate] = {}
    for candidate in candidates:
        existing = merged.get(candidate.dedup_key)
        if existing is None:
            merged[candidate.dedup_key] = candidate
            continue
        for provenance in candidate.provenance:
            if provenance not in existing.provenance:
                existing.provenance.append(provenance)
    return list(merged.values())


class HttpRetrievalAdapter:
    """Retrieves documents over HTTP with full provenance metadata."""

    def __init__(self, timeout_seconds: float = 10.0):
        self._timeout = timeout_seconds

    def retrieve(self, url: str, source_id: str | None = None) -> Candidate:
        retrieved_at = datetime.now(timezone.utc).isoformat()
        try:
            response = httpx.get(url, timeout=self._timeout, follow_redirects=True)
        except httpx.HTTPError:
            return Candidate(
                url=url, title="", content="", retrieved_at=retrieved_at,
                digest="", dedup_key=dedup_key(url, ""),
                source_id=source_id or canonical_url(url),
                access_status="inaccessible", freshness="stale",
            )
        if response.status_code != 200:
            return Candidate(
                url=url, title="", content="", retrieved_at=retrieved_at,
                digest="", dedup_key=dedup_key(url, ""),
                source_id=source_id or canonical_url(url),
                access_status="inaccessible", freshness="stale",
            )
        content = response.text
        return Candidate(
            url=url,
            title=content.splitlines()[0][:120] if content else "",
            content=content,
            retrieved_at=retrieved_at,
            digest=content_digest(content),
            dedup_key=dedup_key(url, content),
            source_id=source_id or canonical_url(url),
            provenance=[{"url": url, "retrieved_at": retrieved_at}],
        )

    def refetch_digest(self, url: str) -> tuple[str | None, str]:
        """Independently refetch: returns (digest, status). Digest None with
        status 'inaccessible' means the prior evidence must not be claimed
        fresh (CTX-005/CTX-002 recovery semantics)."""
        try:
            response = httpx.get(url, timeout=self._timeout, follow_redirects=True)
        except httpx.HTTPError:
            return None, "inaccessible"
        if response.status_code != 200:
            return None, "inaccessible"
        return content_digest(response.text), "accessible"
