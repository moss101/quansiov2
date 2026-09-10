"""Real HTTP actuation target for M5 effect tests.

Records idempotency-keyed submissions; supports an ambiguous endpoint that
processes the request but never responds (timeout -> UNKNOWN), and a probe
endpoint reporting the recorded idempotency state.
"""

from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlparse


class EffectTargetHandler(BaseHTTPRequestHandler):
    # class state: recorded submissions keyed by idempotency key
    recorded: dict = {}
    delay_seconds: float = 0.0

    def log_message(self, *args):  # noqa: D102 - silence
        pass

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        key = dict(parse_qsl(body)).get("idempotency_key") or self.headers.get("Idempotency-Key", "")
        type(self).recorded[key] = {
            "body": body,
            "received_at": time.time(),
            "responses": type(self).recorded.get(key, {}).get("responses", 0) + 1,
        }
        if type(self).delay_seconds > 0:
            time.sleep(type(self).delay_seconds)
            # Ambiguous: processed but the connection is dropped unanswered.
            self.close_connection = True
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"accepted": true, "receipt": "rcpt-' + key.encode() + b'"}')

    def do_GET(self):  # noqa: N802 - idempotency probe
        key = dict(parse_qsl(urlparse(self.path).query)).get("idempotency_key", "")
        entry = type(self).recorded.get(key)
        state = "committed" if entry else "not_found"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"idempotency_state": state}).encode())


def start_effect_target(delay_seconds: float = 0.0):
    handler = type("Handler", (EffectTargetHandler,),
                   {"recorded": {}, "delay_seconds": delay_seconds})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port, handler.recorded
