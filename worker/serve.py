"""pf-worker HTTP surface: health + the (soon) single commit gate endpoint.

/commit is a deliberate 501 until the Postgres Store adapter lands (Phase 2).
Fail loud, never pretend.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {
                "status": "ok",
                "genesis_root_hash": os.environ.get("POWERFARM_GENESIS_ROOT", "unset"),
            })
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/commit":
            self._send(501, {"error": "commit gate store adapter not wired yet (Phase 2)"})
            return
        self._send(404, {"error": "not found"})

    def _send(self, status: int, body: dict[str, object]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        pass  # structured logging lands with the worker phase


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
