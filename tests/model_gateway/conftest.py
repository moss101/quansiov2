"""Model gateway test fixtures: real llama.cpp provider + protocol stubs."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LLAMA_SERVER = "/opt/homebrew/bin/llama-server"
MODEL_PATH = "/Users/mohsin/cursor/quansio beta/quansio/models/LFM2.5-VL-3B-Q4_K_M.gguf"
PROVIDER_PORT = 54340
PROVIDER_BASE = f"http://127.0.0.1:{PROVIDER_PORT}"


def _provider_healthy() -> bool:
    try:
        response = httpx.get(f"{PROVIDER_BASE}/health", timeout=2)
        return response.json().get("status") == "ok"
    except Exception:  # noqa: BLE001
        return False


@pytest.fixture(scope="session")
def real_provider():
    """The real local provider boundary: llama.cpp serving a real model."""
    if not Path(LLAMA_SERVER).is_file() or not Path(MODEL_PATH).is_file():
        raise AssertionError(
            "MOD-008 requires the real provider boundary; it is unavailable on this host"
        )
    started_here = False
    process = None
    if not _provider_healthy():
        process = subprocess.Popen(
            [LLAMA_SERVER, "-m", MODEL_PATH, "--host", "127.0.0.1", "--port", str(PROVIDER_PORT),
             "--alias", "quansio-local-lfm"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        started_here = True
        deadline = time.time() + 180
        while time.time() < deadline:
            if _provider_healthy():
                break
            if process.poll() is not None:
                raise AssertionError("llama-server exited during startup")
            time.sleep(2)
        else:
            raise AssertionError("llama-server did not become healthy")
    yield PROVIDER_BASE
    if started_here and process is not None:
        process.terminate()
        process.wait(timeout=30)


class _StubHandler(BaseHTTPRequestHandler):
    """Configurable protocol-abuse server for adapter contract tests."""

    behavior = "missing_usage"  # missing_usage | malformed_json | http_500 | http_429 | no_terminal

    def log_message(self, *args):  # noqa: D102 - silence
        pass

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        behavior = type(self).behavior
        if behavior == "http_500":
            self.send_response(500)
            self.end_headers()
            return
        if behavior == "http_429":
            self.send_response(429)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        if behavior == "malformed_json":
            self.wfile.write(b"data: {not json}\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
        elif behavior == "missing_usage":
            self.wfile.write(b'data: {"choices":[{"delta":{"role":"assistant"},"index":0}]}\n\n')
            self.wfile.write(b'data: {"choices":[{"delta":{"content":"hi"},"index":0}]}\n\n')
            self.wfile.write(b'data: {"choices":[{"delta":{},"index":0,"finish_reason":"stop"}]}\n\n')
            self.wfile.write(b"data: [DONE]\n\n")
        elif behavior == "no_terminal":
            self.wfile.write(b'data: {"choices":[{"delta":{"content":"hi"},"index":0}]}\n\n')
            self.wfile.write(b"data: [DONE]\n\n")


@pytest.fixture(scope="session")
def stub_provider_factory():
    servers = []

    def factory(behavior: str) -> str:
        handler = type("Handler", (_StubHandler,), {"behavior": behavior})
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        return f"http://127.0.0.1:{port}"

    yield factory
    for server in servers:
        server.shutdown()
