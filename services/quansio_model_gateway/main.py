"""quansio-model-gateway deployable entrypoint."""

from __future__ import annotations

from quansio.platform.db import PlatformDatabase, database_config
from quansio.model_gateway.gateway import ModelGateway

database = PlatformDatabase(database_config())
gateway = ModelGateway(database)


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI(title="quansio-model-gateway", version="9.0.0")

    @app.get("/healthz")
    def healthz():
        return {"status": "live", "service": "quansio-model-gateway"}

    uvicorn.run(app, host="127.0.0.1", port=8082)
