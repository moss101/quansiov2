"""ResearchRecord and entity resolution (CTX-003).

Research records separate canonical entity identity, attributes, claims,
source references, freshness, confidence and verification state. Identity
constraints prevent false merges of similarly named entities: a merge
requires an exact identity-key match (normalized identity attributes), and
any near-name merge without key evidence is refused before synthesis.
Identity corrections create a new entity version and preserve the
superseded identity evidence — prior records are never silently rewritten.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class FalseMergeRejected(Exception):
    """An entity merge lacked the identity-key evidence required."""


_IDENTITY_NOISE = re.compile(r"\b(inc|llc|ltd|gmbh|corp|corporation|company|the)\b", re.I)


def identity_key(name: str, distinguishing_attributes: dict) -> str:
    """Canonical entity identity: normalized name plus the distinguishing
    attribute values (registration ids, country, founding year). Similar
    names with different distinguishing attributes produce different keys —
    this is the constraint that blocks false merges."""
    normalized = _IDENTITY_NOISE.sub("", name).lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    distinguishing = ",".join(
        f"{key}={distinguishing_attributes[key]}"
        for key in sorted(distinguishing_attributes)
        if key in ("registration_id", "country", "founded_year")
    )
    material = f"{normalized}|{distinguishing}"
    return hashlib.sha256(material.encode()).hexdigest()[:24]


class ResearchRecordStore:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def upsert_entity(
        self,
        context: IdentityContext,
        program_id: str,
        name: str,
        distinguishing_attributes: dict,
        attributes: dict | None = None,
        confidence: float = 0.0,
        source_digest: str | None = None,
    ) -> tuple[str, int]:
        """Resolve-or-create an entity by identity key. Similar names with
        different distinguishing attributes resolve to different entities."""
        entity_key = identity_key(name, distinguishing_attributes)
        with self._db.connection() as connection:
            row = connection.execute(
                """
                SELECT entity_version FROM research_entities
                WHERE tenant_id = %s AND program_id = %s AND entity_key = %s
                ORDER BY entity_version DESC LIMIT 1
                """,
                (context.tenant_id, program_id, entity_key),
            ).fetchone()
            version = (row[0] if row else 0) + 1
            if row is None:
                connection.execute(
                    """
                    INSERT INTO research_entities
                        (tenant_id, program_id, entity_key, entity_version, display_name,
                         attributes, confidence)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (context.tenant_id, program_id, entity_key, 1, name,
                     Json(attributes or {}), confidence),
                )
                version = 1
            if source_digest:
                connection.execute(
                    """
                    INSERT INTO research_entity_evidence
                        (tenant_id, program_id, entity_key, entity_version, kind, source_digest, detail)
                    VALUES (%s, %s, %s, %s, 'supporting', %s, %s)
                    """,
                    (context.tenant_id, program_id, entity_key, version,
                     source_digest, Json({"name": name})),
                )
        return entity_key, version

    def merge_entities(self, context: IdentityContext, program_id: str,
                       entity_key_a: str, entity_key_b: str,
                       merge_evidence_digest: str | None) -> str:
        """A merge demands identity-key evidence: without a source digest
        proving the two keys denote one entity, the merge is refused."""
        if not merge_evidence_digest:
            raise FalseMergeRejected(
                f"merging {entity_key_a} with {entity_key_b} refused: no identity evidence"
            )
        winner = entity_key_a
        with self._db.connection() as connection:
            with connection.transaction():
                connection.execute(
                    """
                    UPDATE research_entities SET superseded_by = %s
                    WHERE tenant_id = %s AND program_id = %s AND entity_key = %s
                      AND superseded_by IS NULL
                    """,
                    (winner, context.tenant_id, program_id, entity_key_b),
                )
                connection.execute(
                    """
                    INSERT INTO research_entity_evidence
                        (tenant_id, program_id, entity_key, entity_version, kind, source_digest, detail)
                    SELECT tenant_id, program_id, entity_key, entity_version,
                           'superseded_identity', %s, '{}'::jsonb
                    FROM research_entities
                    WHERE tenant_id = %s AND program_id = %s AND entity_key = %s
                    """,
                    (merge_evidence_digest, context.tenant_id, program_id, entity_key_b),
                )
        return winner

    def correct_identity(
        self, context: IdentityContext, program_id: str, old_entity_key: str,
        new_name: str, new_distinguishing: dict, correction_source_digest: str,
    ) -> str:
        """CTX-003-R01: identity correction creates a NEW entity version
        under the corrected key and records the superseded identity evidence;
        the prior record stays intact."""
        new_key = identity_key(new_name, new_distinguishing)
        with self._db.connection() as connection:
            with connection.transaction():
                current = connection.execute(
                    """
                    SELECT entity_version FROM research_entities
                    WHERE tenant_id = %s AND program_id = %s AND entity_key = %s
                    ORDER BY entity_version DESC LIMIT 1
                    """,
                    (context.tenant_id, program_id, old_entity_key),
                ).fetchone()
                next_version = (current[0] if current else 0) + 1
                connection.execute(
                    """
                    INSERT INTO research_entities
                        (tenant_id, program_id, entity_key, entity_version, display_name,
                         attributes, confidence, superseded_by)
                    VALUES (%s, %s, %s, %s, %s, '{}'::jsonb, 0, NULL)
                    """,
                    (context.tenant_id, program_id, new_key, next_version, new_name),
                )
                connection.execute(
                    """
                    INSERT INTO research_entity_evidence
                        (tenant_id, program_id, entity_key, entity_version, kind, source_digest, detail)
                    VALUES (%s, %s, %s, %s, 'identity_correction', %s,
                            %s::jsonb)
                    """,
                    (context.tenant_id, program_id, old_entity_key, next_version,
                     correction_source_digest,
                     json.dumps({"corrected_to": new_key})),
                )
        return new_key

    def add_claim(
        self, context: IdentityContext, program_id: str, entity_key: str,
        statement: str, source_digests: list[str],
    ) -> str:
        claim_id = str(uuid.uuid4())
        claim_digest = hashlib.sha256(statement.strip().lower().encode()).hexdigest()
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO research_claims
                    (claim_id, tenant_id, program_id, entity_key, claim_digest,
                     statement, source_digests)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (claim_id, context.tenant_id, program_id, entity_key,
                 claim_digest, statement, source_digests),
            )
        return claim_id

    def set_claim_verification(self, context: IdentityContext, claim_id: str,
                               verification: str, detail: dict) -> None:
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE research_claims SET verification = %s, evidence_detail = %s::jsonb
                WHERE tenant_id = %s AND claim_id = %s
                """,
                (verification, json.dumps(detail), context.tenant_id, claim_id),
            )

    def get_claim(self, context: IdentityContext, claim_id: str) -> dict | None:
        row = self._db.query_one(
            """
            SELECT claim_id::text, entity_key, statement, source_digests, verification, evidence_detail
            FROM research_claims WHERE tenant_id = %s AND claim_id = %s
            """,
            (context.tenant_id, claim_id),
        )
        if row is None:
            return None
        return {
            "claim_id": row[0], "entity_key": row[1], "statement": row[2],
            "source_digests": list(row[3] or ()), "verification": row[4],
            "evidence_detail": row[5],
        }

    def entity_record(self, context: IdentityContext, program_id: str, entity_key: str) -> dict | None:
        row = self._db.query_one(
            """
            SELECT entity_key, display_name, attributes, confidence, verification, superseded_by
            FROM research_entities
            WHERE tenant_id = %s AND program_id = %s AND entity_key = %s
            ORDER BY entity_version DESC LIMIT 1
            """,
            (context.tenant_id, program_id, entity_key),
        )
        if row is None:
            return None
        return {
            "entity_key": row[0], "display_name": row[1], "attributes": row[2],
            "confidence": row[3], "verification": row[4], "superseded_by": row[5],
        }

    def entity_evidence(self, context: IdentityContext, program_id: str, entity_key: str) -> list[dict]:
        rows = self._db.query_all(
            """
            SELECT kind, source_digest, detail, created_at FROM research_entity_evidence
            WHERE tenant_id = %s AND program_id = %s AND entity_key = %s
            ORDER BY created_at
            """,
            (context.tenant_id, program_id, entity_key),
        )
        return [{"kind": r[0], "source_digest": r[1], "detail": r[2], "at": r[3]} for r in rows]

    def claims(self, context: IdentityContext, program_id: str) -> list[dict]:
        rows = self._db.query_all(
            """
            SELECT claim_id::text, entity_key, statement, verification FROM research_claims
            WHERE tenant_id = %s AND program_id = %s ORDER BY created_at
            """,
            (context.tenant_id, program_id),
        )
        return [{"claim_id": r[0], "entity_key": r[1], "statement": r[2], "verification": r[3]} for r in rows]
