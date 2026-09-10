"""Shared corpus server for context/research qualification.

Serves a deterministic corpus of company pages over real HTTP. Each page
carries extraction lines (``CLAIM:``) and known ground truth; some pages are
duplicates of others under different URLs (dedup semantics), one page is
designed to be taken offline mid-qualification (inaccessible transitions).
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def build_corpus() -> dict[str, str]:
    """Deterministic corpus: 120 company pages, 8 of them relevant with
    verifiable claims; 4 duplicate mirrors; 1 page that will be removed."""
    pages: dict[str, str] = {}
    for i in range(120):
        path = f"/companies/company-{i:03d}"
        relevant = i < 8
        lines = [f"Company {i:03d} profile", ""]
        if relevant:
            lines.append(f"CLAIM: company-{i:03d} operates in the energy sector")
            lines.append(f"CLAIM: company-{i:03d} was founded in {1990 + i}")
            lines.append(f"CONTACT: contact-{i:03d}@energy-corp.example")
        else:
            lines.append(f"Company {i:03d} publishes generic information only.")
        pages[path] = "\n".join(lines)
    # Duplicates: mirrors of company-000..003 under different paths.
    for j in range(4):
        pages[f"/mirror-{j}"] = pages[f"/companies/company-{j:03d}"]
    # Page designed to disappear (inaccessible transition).
    pages["/vanishing/first"] = "CLAIM: vanishing-source was accessible at extraction time"
    return pages


class CorpusHandler(BaseHTTPRequestHandler):
    pages: dict[str, str] = {}
    removed: set[str] = set()

    def log_message(self, *args):  # noqa: D102 - silence
        pass

    def do_GET(self):  # noqa: N802
        path = self.path.split("?")[0]
        if path in type(self).removed:
            self.send_response(404)
            self.end_headers()
            return
        body = type(self).pages.get(path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())


def start_corpus_server():
    pages = build_corpus()
    handler = type("Handler", (CorpusHandler,), {"pages": pages, "removed": set()})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port, pages
