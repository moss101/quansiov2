"""quansio-artifact HTTP surface: immutable artifact and evidence storage.

Content is addressed by sha256; blobs live in MinIO and metadata in
PostgreSQL. Upload verifies digest identity, downloads re-verify the stored
bytes against the digest, and quarantined artifacts are unreadable.
"""

from __future__ import annotations

import io

from fastapi import FastAPI, Header, HTTPException, Request, Response
from minio import Minio

from quansio.artifact.store import ArtifactIntegrityError, ArtifactStore
from quansio.control.identity import ControlService
from quansio.platform.db import PlatformDatabase, database_config, load_qualenv_passwords
from quansio.platform.service import (
    add_cors,
    add_health_routes,
    default_database,
    identity_view,
    resolve_bearer,
)


def _minio_client() -> Minio:
    material = load_qualenv_passwords()
    return Minio(
        "127.0.0.1:54331",
        access_key="quansio_qual_admin",
        secret_key=material["QUAL_MINIO_PASSWORD"],
        secure=False,
    )


def create_app(database: PlatformDatabase | None = None,
               client: Minio | None = None) -> FastAPI:
    app = FastAPI(title="quansio-artifact", version="9.0.0")
    add_cors(app)
    db = database or default_database()
    control = ControlService(db)
    store = ArtifactStore(db, client or _minio_client())

    add_health_routes(app, db, "quansio-artifact")

    @app.put("/v9/artifacts")
    async def put_artifact(
        request: Request,
        content_type: str = Header(default="application/octet-stream"),
        authorization: str = Header(default=""),
    ) -> dict:
        context = resolve_bearer(authorization, control)
        data = await request.body()
        if not data:
            raise HTTPException(status_code=422, detail="empty artifact body")
        result = store.put(context, data, content_type)
        return {"artifact": result, "identity": identity_view(context)}

    @app.get("/v9/artifacts/{digest}/metadata")
    def artifact_metadata(digest: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            _, metadata = store.get(context, digest)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ArtifactIntegrityError as error:
            raise HTTPException(status_code=423, detail=str(error)) from error
        return {"digest": digest, "metadata": metadata}

    @app.get("/v9/artifacts/{digest}")
    def get_artifact(digest: str, authorization: str = Header(default="")) -> Response:
        context = resolve_bearer(authorization, control)
        try:
            data, metadata = store.get(context, digest)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ArtifactIntegrityError as error:
            raise HTTPException(status_code=423, detail=str(error)) from error
        return Response(
            content=data,
            media_type=metadata["media_type"],
            headers={"X-Artifact-Scan-State": metadata["scan_state"]},
        )

    @app.post("/v9/artifacts/{digest}/scan")
    def mark_scan(digest: str, state: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            store.mark_scanned(context, digest, state)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"digest": digest, "scan_state": state}

    @app.post("/v9/artifacts/restore")
    def restore_artifact(backup_row: dict, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        scan_state = store.restore_metadata_from_backup(context, backup_row)
        return {"digest": backup_row["digest"], "scan_state": scan_state}

    return app
