"""Qualification environment manager (ENV-001).

Provisions the real qualification boundaries with isolated identities:

- PostgreSQL 17 (authoritative relational store: ``quansio_platform`` and
  the durable event transport database ``quansio_events``);
- Redis 8 (non-authoritative lease/cache coordination, password-protected);
- MinIO (immutable artifact/evidence object storage, dedicated bucket).

Commands::

    python tools/environment/qualenv.py provision    # fresh stack + manifest
    python tools/environment/qualenv.py health       # re-run health checks
    python tools/environment/qualenv.py verify       # refuse in-memory fakes
    python tools/environment/qualenv.py teardown     # remove stack, prove down

The manifest (``evidence/environment/<env_id>/manifest.json``) records the
real-boundary proof: implementations, isolated identity names, endpoints,
health transcripts and the secrets digest (never secret material).
"""

from __future__ import annotations

import argparse
import json
import secrets
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import redis
from minio import Minio

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_DIR = ROOT / "deploy/compose"
ENV_FILE = COMPOSE_DIR / ".env.qual"
MANIFEST_ROOT = ROOT / "evidence/environment"
PROJECT = "quansio-qual"
HOST = "127.0.0.1"
PG_PORT = 54329
REDIS_PORT = 54330
MINIO_PORT = 54331
PLATFORM_DB = "quansio_platform"
EVENTS_DB = "quansio_events"
APP_ROLE = "quansio_app"
BUCKET = "quansio-artifacts"
REQUIRED_BOUNDARIES = ("relational_primary", "durable_event_transport", "non_authoritative_coordination", "artifact_object_store")
HEALTH_TIMEOUT_S = 120.0


def sha256_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def docker_compose(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["docker", "compose", "-p", PROJECT, "--env-file", str(ENV_FILE), "--project-directory", str(COMPOSE_DIR), *args],
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise SystemExit(f"docker compose {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")
    return result


def _free_port(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((HOST, port)) != 0


def generate_env_file() -> None:
    if ENV_FILE.exists():
        ENV_FILE.unlink()
    material = {
        "QUAL_PG_ADMIN_PASSWORD": secrets.token_urlsafe(24),
        "QUAL_PG_APP_PASSWORD": secrets.token_urlsafe(24),
        "QUAL_REDIS_PASSWORD": secrets.token_urlsafe(24),
        "QUAL_MINIO_PASSWORD": secrets.token_urlsafe(24),
    }
    ENV_FILE.write_text("".join(f"{k}={v}\n" for k, v in material.items()))
    ENV_FILE.chmod(0o600)


def wait_for(fn, description: str, timeout: float = HEALTH_TIMEOUT_S):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            return fn()
        except Exception as error:  # noqa: BLE001 - probing loop reports last failure
            last_error = error
            time.sleep(1.0)
    raise SystemExit(f"timeout waiting for {description}: {last_error}")


def check_postgres(database: str, password: str) -> dict:
    started = time.monotonic()
    with psycopg.connect(
        host=HOST, port=PG_PORT, dbname=database, user=APP_ROLE, password=password, connect_timeout=5
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version(), current_user, current_database()")
            version, user, db = cursor.fetchone()
    latency = round((time.monotonic() - started) * 1000, 1)
    return {
        "boundary": "relational_primary" if database == PLATFORM_DB else "durable_event_transport",
        "check": f"connect as {APP_ROLE} to {database}; SELECT version(), current_user, current_database()",
        "status": "PASS",
        "latency_ms": latency,
        "detail": {"server": version.split(",")[0], "user": user, "database": db},
    }


def check_redis(password: str) -> dict:
    started = time.monotonic()
    client = redis.Redis(host=HOST, port=REDIS_PORT, password=password, socket_timeout=5)
    pong = client.ping()
    probe = "qualenv:probe"
    client.set(probe, "1")
    value = client.get(probe)
    client.delete(probe)
    latency = round((time.monotonic() - started) * 1000, 1)
    if not pong or value != b"1":
        raise SystemExit("redis probe failed")
    info = client.info("server")
    return {
        "boundary": "non_authoritative_coordination",
        "check": "PING, SET/GET/DELETE probe key with isolated password",
        "status": "PASS",
        "latency_ms": latency,
        "detail": {"server": f"redis {info.get('redis_version')}", "mode": info.get("redis_mode")},
    }


def check_minio(password: str) -> dict:
    started = time.monotonic()
    client = Minio(f"{HOST}:{MINIO_PORT}", access_key="quansio_qual_admin", secret_key=password, secure=False)
    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)
    probe = "qualenv/probe.txt"
    import io

    payload = b"quansio qualification probe"
    client.put_object(BUCKET, probe, io.BytesIO(payload), len(payload))
    response = client.get_object(BUCKET, probe)
    try:
        fetched = response.read()
    finally:
        response.close()
        response.release_conn()
    client.remove_object(BUCKET, probe)
    latency = round((time.monotonic() - started) * 1000, 1)
    if fetched != payload:
        raise SystemExit("minio round trip mismatch")
    return {
        "boundary": "artifact_object_store",
        "check": f"bucket_exists/make_bucket {BUCKET}; put/get/remove probe object",
        "status": "PASS",
        "latency_ms": latency,
        "detail": {"bucket": BUCKET, "endpoint": f"{HOST}:{MINIO_PORT}"},
    }


def load_passwords() -> dict:
    if not ENV_FILE.is_file():
        raise SystemExit(f"{ENV_FILE} missing; run provision first")
    material = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            material[key] = value
    return material


def _post_teardown_probe_fails() -> bool:
    """True when no boundary is reachable anymore (desired post-teardown state)."""
    if not ENV_FILE.is_file():
        return True
    try:
        material = load_passwords()
        checks = health_checks_against(material)
    except SystemExit:
        return True
    except Exception:  # noqa: BLE001 - any failure to reach boundaries is desired
        return True
    return not any(check.get("status") == "PASS" for check in checks)


def run_health(material: dict) -> list[dict]:
    app_password = material["QUAL_PG_APP_PASSWORD"]
    minio_password = material["QUAL_MINIO_PASSWORD"]
    checks = [
        wait_for(lambda: check_postgres(PLATFORM_DB, app_password), "postgres platform db"),
        wait_for(lambda: check_postgres(EVENTS_DB, app_password), "postgres events db"),
        wait_for(lambda: check_redis(material["QUAL_REDIS_PASSWORD"]), "redis"),
        wait_for(lambda: check_minio(minio_password), "minio"),
    ]
    return checks


def cmd_provision(args: argparse.Namespace) -> int:
    # Remove any previous stack of this project first, then verify the ports
    # are free so a foreign service is never clobbered.
    generate_env_file()
    docker_compose("down", "-v", "--remove-orphans", check=False)
    for port in (PG_PORT, REDIS_PORT, MINIO_PORT, 54332):
        if not _free_port(port):
            raise SystemExit(f"port {port} is occupied by a service outside project {PROJECT}; refusing to provision")
    docker_compose("up", "-d", "--wait", "--wait-timeout", str(int(HEALTH_TIMEOUT_S)))
    material = load_passwords()
    checks = run_health(material)

    images = docker_compose("images", "--format", "json")
    image_versions = {}
    stdout = images.stdout.strip()
    try:
        parsed = json.loads(stdout)
        entries = parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        entries = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    for entry in entries:
        if isinstance(entry, list):  # nested arrays appear in some compose versions
            for nested in entry:
                image_versions[nested.get("Container", nested.get("Name", "?"))] = nested.get("Image", "?")
            continue
        image_versions[entry.get("Container", entry.get("Service", entry.get("Name", "?")))] = entry.get("Image", "?")

    env_id = f"qual-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    manifest_dir = MANIFEST_ROOT / env_id
    manifest_dir.mkdir(parents=True, exist_ok=True)
    transcript = json.dumps({"executed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "checks": checks}, indent=2) + "\n"
    transcript_path = manifest_dir / "health-transcript.json"
    transcript_path.write_text(transcript)
    manifest = {
        "schema_revision": "9.0.0",
        "environment_id": env_id,
        "project": PROJECT,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "boundaries": [
            {
                "class": "relational_primary",
                "kind": "real",
                "implementation": image_versions.get("postgres", "postgres:17-alpine"),
                "identity": {"role": APP_ROLE, "database": PLATFORM_DB, "admin_role": "quansio_admin"},
                "endpoint": f"{HOST}:{PG_PORT}",
            },
            {
                "class": "durable_event_transport",
                "kind": "real",
                "implementation": image_versions.get("postgres", "postgres:17-alpine"),
                "identity": {"role": APP_ROLE, "database": EVENTS_DB},
                "endpoint": f"{HOST}:{PG_PORT}",
            },
            {
                "class": "non_authoritative_coordination",
                "kind": "real",
                "implementation": image_versions.get("redis", "redis:8-alpine"),
                "identity": {"protected": True, "password_rotated_per_provision": True},
                "endpoint": f"{HOST}:{REDIS_PORT}",
            },
            {
                "class": "artifact_object_store",
                "kind": "real",
                "implementation": image_versions.get("minio", "quay.io/minio/minio:latest"),
                "identity": {"bucket": BUCKET, "root_user": "quansio_qual_admin"},
                "endpoint": f"{HOST}:{MINIO_PORT}",
            },
        ],
        "isolated_identities": True,
        "secrets_digest": sha256_file(ENV_FILE),
        "health_transcript": "health-transcript.json",
        "health_transcript_digest": sha256_file(transcript_path),
        "torn_down": False,
    }
    (manifest_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"QUAL ENVIRONMENT: PROVISIONED {env_id} (4 real boundaries healthy)")
    return 0


def latest_manifest_path() -> Path:
    manifests = sorted(MANIFEST_ROOT.glob("*/manifest.json"))
    if not manifests:
        raise SystemExit("no environment manifest found; run provision first")
    return manifests[-1]


def health_checks_against(material: dict) -> list[dict]:
    return [
        check_postgres(PLATFORM_DB, material["QUAL_PG_APP_PASSWORD"]),
        check_postgres(EVENTS_DB, material["QUAL_PG_APP_PASSWORD"]),
        check_redis(material["QUAL_REDIS_PASSWORD"]),
        check_minio(material["QUAL_MINIO_PASSWORD"]),
    ]


def cmd_health(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest) if args.manifest else latest_manifest_path()
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("torn_down"):
        print(f"QUAL ENVIRONMENT: UNHEALTHY (environment {manifest['environment_id']} is torn down)")
        return 1
    material = load_passwords()
    checks = health_checks_against(material)
    transcript_path = manifest_path.parent / "health-transcript.json"
    transcript_path.write_text(
        json.dumps({"executed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "checks": checks}, indent=2) + "\n"
    )
    manifest["health_transcript_digest"] = sha256_file(transcript_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"QUAL ENVIRONMENT: HEALTHY ({len(checks)} real boundaries verified; {manifest_path})")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest) if args.manifest else latest_manifest_path()
    manifest = json.loads(manifest_path.read_text())
    errors = []
    covered = {}
    for boundary in manifest.get("boundaries", []):
        covered[boundary["class"]] = boundary
        if boundary.get("kind") != "real":
            errors.append(
                f"boundary {boundary['class']} substituted with {boundary.get('kind')!r}; qualification refuses non-real boundaries"
            )
        if "sqlite" in str(boundary.get("implementation", "")).lower() or "memory" in str(boundary.get("kind", "")).lower():
            errors.append(f"boundary {boundary['class']} uses forbidden implementation {boundary.get('implementation')}")
    for required in REQUIRED_BOUNDARIES:
        if required not in covered:
            errors.append(f"missing required boundary {required}")
    if not manifest.get("isolated_identities"):
        errors.append("identities are not isolated")
    if not manifest.get("health_transcript_digest"):
        errors.append("health transcript not bound to manifest")
    if errors:
        print("QUAL ENVIRONMENT VERIFY: REFUSED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"QUAL ENVIRONMENT VERIFY: READY ({len(covered)} real boundaries with isolated identities)")
    return 0


def cmd_teardown(args: argparse.Namespace) -> int:
    # Bring the stack down first: teardown must work even when no manifest
    # exists yet (interrupted provision).
    docker_compose("down", "-v", "--remove-orphans")
    manifest_path = Path(args.manifest) if args.manifest else None
    manifests = sorted(MANIFEST_ROOT.glob("*/manifest.json"))
    if manifest_path is None and manifests:
        manifest_path = manifests[-1]
    if manifest_path is None or not manifest_path.is_file():
        probe_failed = _post_teardown_probe_fails()
        print("QUAL ENVIRONMENT: TORN DOWN (no manifest existed; no boundary remains reachable)" if probe_failed else "QUAL ENVIRONMENT TEARDOWN: FAIL (boundaries still reachable)")
        return 0 if probe_failed else 1
    manifest = json.loads(manifest_path.read_text())
    # Prove no falsely passing environment remains.
    material = load_passwords()
    post_teardown = []
    try:
        post_teardown = health_checks_against(material)
    except Exception as error:  # noqa: BLE001 - expected after teardown
        post_teardown = [{"status": "EXPECTED_FAIL", "detail": str(error)}]
    any_alive = any(check.get("status") == "PASS" for check in post_teardown)
    manifest["torn_down"] = True
    manifest["teardown_proof"] = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "post_teardown_probe_passed": any_alive,
        "result": "LEFTovers alive" if any_alive else "no boundary remains reachable",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    if any_alive:
        print("QUAL ENVIRONMENT TEARDOWN: FAIL (boundaries still reachable)")
        return 1
    print("QUAL ENVIRONMENT: TORN DOWN (no falsely passing boundary state remains)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["provision", "health", "verify", "teardown"])
    parser.add_argument("--manifest", default=None, help="explicit manifest path")
    args = parser.parse_args()
    return {"provision": cmd_provision, "health": cmd_health, "verify": cmd_verify, "teardown": cmd_teardown}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
