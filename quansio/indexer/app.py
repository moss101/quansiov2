"""quansio-indexer HTTP surface: ingestion, chunking registry, index
freshness, tombstones and rebuild provenance.

Every operation is tenant-scoped from the server-resolved identity; the
indexer never owns model orchestration or business workflow authority.
"""

from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from quansio.control.identity import ControlService
from quansio.indexer.index import IndexDivergence, ResearchIndex
from quansio.platform.db import PlatformDatabase, database_config
from quansio.platform.service import (
    add_health_routes,
    default_database,
    resolve_bearer,
)


class IngestRequest(BaseModel):
    source_id: str
    url: str
    chunks: list[dict]
    revision: int | None = None
    source_gone: bool = False


class FreshnessRequest(BaseModel):
    live_source_ids: list[str]


class RebuildRequest(BaseModel):
    authoritative_sources: list[dict]


def create_app(database: PlatformDatabase | None = None) -> FastAPI:
    app = FastAPI(title="quansio-indexer", version="9.0.0")
    db = database or default_database()
    control = ControlService(db)
    index = ResearchIndex(db)

    add_health_routes(app, db, "quansio-indexer")

    @app.post("/v9/index/ingest")
    def ingest(body: IngestRequest, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            revision = index.ingest(
                context, body.source_id, body.url, body.chunks,
                revision=body.revision, source_gone=body.source_gone,
            )
        except IndexDivergence as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"source_id": body.source_id, "revision": revision}

    @app.post("/v9/index/{source_id}/tombstone")
    def tombstone(source_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        index.tombstone(context, source_id)
        return {"source_id": source_id, "state": "tombstoned"}

    @app.get("/v9/index/query")
    def query(terms: str, include_tombstoned: bool = False, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        found = index.query(context, [t for t in terms.split(",") if t],
                            include_tombstoned=include_tombstoned)
        return {"results": found}

    @app.post("/v9/index/freshness")
    def validate_freshness(body: FreshnessRequest, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        stale = index.validate_freshness(context, set(body.live_source_ids))
        return {"stale_source_ids": stale}

    @app.post("/v9/index/rebuild")
    def rebuild(body: RebuildRequest, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        removed = index.rebuild(context, body.authoritative_sources)
        return {"tombstoned_divergent": removed}

    return app
