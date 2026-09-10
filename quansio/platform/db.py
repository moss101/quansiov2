"""Database configuration and pooled connectivity for the platform.

Configuration comes from environment variables (12-factor). Defaults target
the qualification environment provisioned by ``tools/environment/qualenv.py``
(real PostgreSQL, isolated identities) so every qualification run exercises
the same boundary shape as production.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg_pool import ConnectionPool


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls, database: str = "quansio_platform") -> "DatabaseConfig":
        return cls(
            host=os.environ.get("QUANSIO_PG_HOST", "127.0.0.1"),
            port=int(os.environ.get("QUANSIO_PG_PORT", "54329")),
            database=os.environ.get("QUANSIO_PG_DATABASE", database),
            user=os.environ.get("QUANSIO_PG_USER", "quansio_app"),
            password=os.environ.get("QUANSIO_PG_PASSWORD", ""),
        )

    def conninfo(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.database} "
            f"user={self.user} password={self.password} connect_timeout=5"
        )


def load_qualenv_passwords() -> dict[str, str]:
    """Read the qualification secrets file when env vars are absent."""
    path = Path(__file__).resolve().parents[2] / "deploy/compose/.env.qual"
    material: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                material[key] = value
    return material


def database_config(database: str = "quansio_platform") -> DatabaseConfig:
    config = DatabaseConfig.from_env(database)
    if not config.password:
        config = DatabaseConfig(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=load_qualenv_passwords().get("QUAL_PG_APP_PASSWORD", ""),
        )
    if not config.password:
        raise RuntimeError("no database password configured (QUANSIO_PG_PASSWORD or qualification env file)")
    return config


class PlatformDatabase:
    """Pooled access to one authoritative database."""

    def __init__(self, config: DatabaseConfig, min_size: int = 1, max_size: int = 8):
        self._config = config
        self._pool = ConnectionPool(
            config.conninfo(),
            min_size=min_size,
            max_size=max_size,
            open=True,
            kwargs={"autocommit": False},
        )

    @property
    def config(self) -> DatabaseConfig:
        return self._config

    def connection(self) -> psycopg.Connection:
        return self._pool.connection()

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self.connection() as connection:
            connection.execute(sql, params)

    def query_all(self, sql: str, params: tuple = ()) -> list[tuple]:
        with self.connection() as connection:
            cursor = connection.execute(sql, params)
            return cursor.fetchall()

    def query_one(self, sql: str, params: tuple = ()) -> tuple | None:
        with self.connection() as connection:
            cursor = connection.execute(sql, params)
            return cursor.fetchone()

    def close(self) -> None:
        self._pool.close()
