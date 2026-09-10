"""Independent claim and source verification (CTX-005).

Each claim is verified by independently refetching its cited sources and
comparing the source content digests captured at extraction time against
the refetched digests, plus a term-overlap support check between the claim
statement and the refetched source content. Citation presence alone is
never sufficient: a claim whose statement no longer matches its cited
evidence fails. An inaccessible refetch retains the last evidence digest
and marks the claim stale/inaccessible without fabricating freshness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from quansio.context.retrieval import HttpRetrievalAdapter
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


def term_overlap(statement: str, content: str) -> float:
    statement_terms = {t for t in re.split(r"\W+", statement.lower()) if len(t) > 3}
    if not statement_terms:
        return 0.0
    content_terms = set(re.split(r"\W+", content.lower()))
    hits = sum(1 for term in statement_terms if term in content_terms)
    return hits / len(statement_terms)


@dataclass
class VerificationOutcome:
    claim_id: str
    state: str
    support_score: float
    details: list[dict]


class ClaimVerifier:
    def __init__(self, database: PlatformDatabase, retrieval: HttpRetrievalAdapter,
                 support_threshold: float = 0.5):
        self._db = database
        self._retrieval = retrieval
        self._support_threshold = support_threshold

    def verify(self, context: IdentityContext, program_id: str, claim: dict,
               source_digest_at_extraction: dict[str, str]) -> VerificationOutcome:
        """Refetch every cited source independently and classify the claim.

        ``source_digest_at_extraction`` maps url -> content digest observed
        when the claim was extracted; support scoring compares against it.
        """
        details = []
        states = []
        for url in claim["source_digests"]:
            digest, status = self._retrieval.refetch_digest(url)
            extracted = source_digest_at_extraction.get(url)
            if status == "inaccessible":
                details.append({"url": url, "status": "inaccessible",
                                "last_known_digest": extracted})
                states.append("inaccessible" if extracted else "unsupported")
                continue
            if extracted is None:
                details.append({"url": url, "status": "accessible",
                                "digest": digest, "note": "no extraction-time digest"})
                states.append("unsupported")
                continue
            if digest != extracted:
                details.append({"url": url, "status": "changed",
                                "extracted_digest": extracted, "refetched_digest": digest})
                states.append("stale")
                continue
            overlap = term_overlap(claim["statement"], self._last_content(context, url))
            supported = overlap >= self._support_threshold
            details.append({"url": url, "status": "verified", "digest": digest,
                            "support_score": round(overlap, 3)})
            states.append("supported" if supported else "unsupported")
        if any(state == "conflicting" for state in states):
            final = "conflicting"
        elif states and all(state == "inaccessible" for state in states):
            final = "inaccessible"
        elif "stale" in states:
            final = "stale"
        elif states and all(state == "supported" for state in states):
            final = "supported"
        else:
            final = "unsupported"
        support_score = round(
            sum(1 for s in states if s == "supported") / len(states), 3
        ) if states else 0.0
        outcome = VerificationOutcome(claim["claim_id"], final, support_score, details)
        from quansio.context.research_record import ResearchRecordStore

        ResearchRecordStore(self._db).set_claim_verification(
            context, claim["claim_id"], final,
            {"details": details, "support_score": support_score},
        )
        return outcome

    def _last_content(self, context: IdentityContext, url: str) -> str:
        """Term-overlap support needs the refetched content; the adapter
        caches the most recent refetch body per URL."""
        return self._retrieval.last_content(url)


class ContentCacheAdapter(HttpRetrievalAdapter):
    """Retrieval adapter that remembers the most recent body per canonical
    URL so verification can score support against refetched content."""

    def __init__(self, timeout_seconds: float = 10.0):
        super().__init__(timeout_seconds)
        self._bodies: dict[str, str] = {}

    def retrieve(self, url: str, source_id: str | None = None):
        candidate = super().retrieve(url, source_id)
        if candidate.access_status == "accessible":
            self._bodies[url] = candidate.content
        return candidate

    def refetch_digest(self, url: str) -> tuple[str | None, str]:
        digest, status = super().refetch_digest(url)
        if status == "accessible":
            try:
                import httpx

                response = httpx.get(url, timeout=self._timeout, follow_redirects=True)
                self._bodies[url] = response.text
            except httpx.HTTPError:
                return None, "inaccessible"  # refetch failed mid-verification
        return digest, status

    def last_content(self, url: str) -> str:
        """Body of the most recent successful refetch; empty when the source
        has never been retrieved."""
        return self._bodies.get(url, "")
