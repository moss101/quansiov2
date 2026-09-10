"""Index freshness and tombstone semantics (CTX-007, owner quansio-indexer).

Indexed material carries source revision, chunk provenance and a freshness
watermark. Tombstoned or deleted sources are excluded from queries by
default. Freshness validation detects divergence between the authoritative
source registry and the index (e.g. a source deleted without a tombstone).
A full rebuild from source metadata preserves query identity and freshness
semantics.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase
from quansio.context.retrieval import content_digest


class IndexDivergence(Exception):
    """The index and the authoritative source registry disagree."""


class ResearchIndex:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def ingest(
        self,
        context: IdentityContext,
        source_id: str,
        url: str,
        chunks: list[dict],
        revision: int | None = None,
        source_gone: bool = False,
    ) -> int:
        """Ingest or update a source: chunks are content-addressed and
        stamped with the source revision and a freshness watermark."""
        watermark = datetime.now(timezone.utc)
        with self._db.connection() as connection:
            with connection.transaction():
                row = connection.execute(
                    "SELECT revision FROM index_sources WHERE tenant_id = %s AND source_id = %s",
                    (context.tenant_id, source_id),
                ).fetchone()
                if source_gone:
                    if row is None:
                        connection.execute(
                            """
                            INSERT INTO index_sources
                                (tenant_id, source_id, revision, url, state, freshness_watermark)
                            VALUES (%s, %s, %s, %s, 'tombstoned', %s)
                            """,
                            (context.tenant_id, source_id, revision or 1, "", watermark),
                        )
                        return revision or 1
                    connection.execute(
                        """
                        UPDATE index_sources SET state = 'tombstoned', freshness_watermark = %s
                        WHERE tenant_id = %s AND source_id = %s
                        """,
                        (watermark, context.tenant_id, source_id),
                    )
                    return row[0]
                new_revision = (row[0] + 1) if (row and revision is None) else (revision or 1)
                connection.execute(
                    """
                    INSERT INTO index_sources (tenant_id, source_id, revision, url, state, freshness_watermark)
                    VALUES (%s, %s, %s, %s, 'active', %s)
                    ON CONFLICT (tenant_id, source_id)
                    DO UPDATE SET revision = EXCLUDED.revision, url = EXCLUDED.url,
                                  state = 'active', freshness_watermark = EXCLUDED.freshness_watermark
                    """,
                    (context.tenant_id, source_id, new_revision, url, watermark),
                )
                for index, chunk in enumerate(chunks):
                    text = chunk.get("content", "")
                    connection.execute(
                        """
                        INSERT INTO indexed_chunks
                            (tenant_id, source_id, chunk_id, revision, content, content_digest, provenance)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (tenant_id, source_id, chunk_id)
                        DO UPDATE SET content = EXCLUDED.content,
                                      content_digest = EXCLUDED.content_digest,
                                      revision = EXCLUDED.revision,
                                      provenance = EXCLUDED.provenance,
                                      ingested_at = now()
                        """,
                        (
                            context.tenant_id, source_id,
                            chunk.get("chunk_id", f"{source_id}#chunk-{index}"),
                            new_revision, text, content_digest(text),
                            Json(chunk.get("provenance", {"url": url, "position": index})),
                        ),
                    )
        return new_revision

    def tombstone(self, context: IdentityContext, source_id: str) -> None:
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE index_sources SET state = 'tombstoned', freshness_watermark = now()
                WHERE tenant_id = %s AND source_id = %s
                """,
                (context.tenant_id, source_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(f"unknown source {source_id}")

    def query(self, context: IdentityContext, terms: list[str], include_tombstoned: bool = False) -> list[dict]:
        """Term query over non-tombstoned chunks by default; results carry
        chunk provenance and the freshness watermark of their source."""
        rows = self._db.query_all(
            """
            SELECT c.source_id, c.chunk_id, c.revision, c.content, c.content_digest, c.provenance,
                   s.state, s.freshness_watermark, s.url
            FROM indexed_chunks c
            JOIN index_sources s ON s.tenant_id = c.tenant_id AND s.source_id = c.source_id
            WHERE c.tenant_id = %s
              AND (%s OR s.state = 'active')
              AND (%s = '{}' OR EXISTS (
                    SELECT 1 FROM unnest(%s::text[]) AS term
                    WHERE c.content ILIKE '%%' || term || '%%'))
            ORDER BY c.source_id, c.chunk_id
            """,
            (context.tenant_id, include_tombstoned, terms, terms),
        )
        return [
            {
                "source_id": r[0],
                "chunk_id": r[1],
                "revision": r[2],
                "content": r[3],
                "content_digest": r[4],
                "provenance": r[5],
                "source_state": r[6],
                "freshness_watermark": r[7],
                "url": r[8],
            }
            for r in rows
        ]

    def validate_freshness(self, context: IdentityContext, live_source_ids: set[str]) -> list[str]:
        """Detect divergence: index believes a source is active but the
        authoritative registry no longer lists it (deleted without a
        tombstone)."""
        rows = self._db.query_all(
            "SELECT source_id FROM index_sources WHERE tenant_id = %s AND state = 'active'",
            (context.tenant_id,),
        )
        return [r[0] for r in rows if r[0] not in live_source_ids]

    def rebuild(self, context: IdentityContext, authoritative_sources: list[dict]) -> int:
        """Rebuild the index from authoritative source metadata; query
        identity and freshness semantics are preserved because chunks are
        content-addressed and re-stamped from source revisions."""
        with self._db.connection() as connection:
            connection.execute("DELETE FROM indexed_chunks WHERE tenant_id = %s", (context.tenant_id,))
            connection.execute("DELETE FROM index_sources WHERE tenant_id = %s", (context.tenant_id,))
        rebuilt = 0
        for source in authoritative_sources:
            self.ingest(
                context,
                source_id=source["source_id"],
                url=source["url"],
                chunks=source["chunks"],
                revision=source.get("revision"),
                source_gone=source.get("state") == "tombstoned",
            )
            rebuilt += 1
        return rebuilt
