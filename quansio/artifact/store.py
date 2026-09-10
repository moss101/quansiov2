"""Immutable artifact and evidence storage (DAT-006, owner quansio-artifact).

Content is addressed by sha256: the object key is the digest, so historical
bytes can never be mutated. Metadata lives in PostgreSQL (tenant, media
type, producer, size, scan state, grants); blobs live in MinIO. A restored
metadata row must pass digest verification against the blob before the
artifact becomes readable again (scan_state = 'verified').
"""

from __future__ import annotations

import hashlib
import io
import uuid

import psycopg
from minio import Minio
from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase

BUCKET = "quansio-artifacts"


class ArtifactIntegrityError(Exception):
    """Raised when bytes do not match their recorded digest identity."""


class ArtifactStore:
    def __init__(self, database: PlatformDatabase, minio_client: Minio, bucket: str = BUCKET):
        self._db = database
        self._client = minio_client
        self._bucket = bucket
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    @staticmethod
    def digest_of(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def put(self, context: IdentityContext, data: bytes, media_type: str, grants: dict | None = None) -> dict:
        digest = self.digest_of(data)
        with self._db.connection() as connection:
            existing = connection.execute(
                """
                SELECT digest, size_bytes, scan_state FROM artifact_records WHERE digest = %s
                """,
                (digest,),
            ).fetchone()
            if existing is None:
                self._client.put_object(
                    self._bucket,
                    digest,
                    io.BytesIO(data),
                    len(data),
                    content_type=media_type,
                )
                connection.execute(
                    """
                    INSERT INTO artifact_records
                        (tenant_id, digest, media_type, producer, size_bytes, scan_state, grants)
                    VALUES (%s, %s, %s, %s, %s, 'unscanned', %s)
                    """,
                    (context.tenant_id, digest, media_type, context.user_id, len(data), Json(grants or {})),
                )
            else:
                # Digest identity already exists: verify the stored bytes and
                # refuse any mutation of historical evidence.
                stored = self._fetch_blob(digest)
                if stored != data:
                    raise ArtifactIntegrityError(
                        f"digest collision/mutation attempt for {digest}: bytes differ from historical artifact"
                    )
        return {
            "digest": digest,
            "size_bytes": len(data),
            "media_type": media_type,
            "scan_state": self.scan_state(digest),
        }

    def get(self, context: IdentityContext, digest: str) -> tuple[bytes, dict]:
        row = self._db.query_one(
            """
            SELECT digest, media_type, size_bytes, scan_state, grants
            FROM artifact_records WHERE digest = %s
            """,
            (digest,),
        )
        if row is None:
            raise KeyError(f"unknown artifact {digest}")
        if row[3] == "quarantined":
            raise ArtifactIntegrityError(
                f"artifact {digest} is quarantined; digest could not be verified after restore"
            )
        data = self._fetch_blob(digest)
        if self.digest_of(data) != row[0]:
            raise ArtifactIntegrityError(f"stored bytes no longer match digest {digest}")
        return data, {
            "media_type": row[1],
            "size_bytes": row[2],
            "scan_state": row[3],
            "grants": row[4],
        }

    def _fetch_blob(self, digest: str) -> bytes:
        response = self._client.get_object(self._bucket, digest)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def scan_state(self, digest: str) -> str:
        row = self._db.query_one("SELECT scan_state FROM artifact_records WHERE digest = %s", (digest,))
        return row[0] if row else "unknown"

    def mark_scanned(self, context: IdentityContext, digest: str, state: str) -> None:
        if state not in {"unscanned", "verified", "quarantined"}:
            raise ValueError(f"invalid scan state {state}")
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE artifact_records SET scan_state = %s WHERE digest = %s",
                (state, digest),
            )

    def restore_metadata_from_backup(self, context: IdentityContext, backup_row: dict) -> str:
        """Restore one metadata row from backup; digest-verify before readable.

        The restored artifact is readable (scan_state='verified') only if the
        referenced blob exists in object storage and hashes to its digest.
        """
        digest = backup_row["digest"]
        blob_ok = True
        try:
            stored = self._fetch_blob(digest)
            blob_ok = self.digest_of(stored) == digest
        except Exception:  # noqa: BLE001 - missing blob leaves artifact unreadable
            blob_ok = False
        scan_state = "verified" if blob_ok else "quarantined"
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO artifact_records
                    (tenant_id, digest, media_type, producer, size_bytes, scan_state, grants)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, digest) DO UPDATE SET scan_state = EXCLUDED.scan_state
                """,
                (
                    backup_row["tenant_id"],
                    digest,
                    backup_row["media_type"],
                    backup_row["producer"],
                    backup_row["size_bytes"],
                    scan_state,
                    Json(backup_row.get("grants", {})),
                ),
            )
        return scan_state
