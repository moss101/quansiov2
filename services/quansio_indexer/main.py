"""quansio-indexer deployable entrypoint."""

from quansio.platform.db import PlatformDatabase, database_config

database = PlatformDatabase(database_config())

if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI(title="quansio-indexer", version="9.0.0")

    @app.get("/healthz")
    def healthz():
        return {"status": "live", "service": "quansio-indexer"}

    uvicorn.run(app, host="127.0.0.1", port=8084)
