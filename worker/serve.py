"""pf-worker HTTP surface: health + the (soon) single commit gate endpoint.

/commit is a deliberate 501 until the Postgres Store adapter lands (Phase 2).
Fail loud, never pretend.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .github_webhook import MAX_BODY_BYTES, WebhookError, accept_delivery


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
        if self.path == "/integrations/github/webhook":
            self._github_webhook()
            return
        if self.path == "/commit":
            self._send(501, {"error": "commit gate store adapter not wired yet (Phase 2)"})
            return
        self._send(404, {"error": "not found"})

    def _github_webhook(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send(411, {"error": "valid Content-Length required"})
            return
        if content_length < 0 or content_length > MAX_BODY_BYTES:
            self._send(413, {"error": "payload too large"})
            return
        body = self.rfile.read(content_length)
        home = Path(os.environ.get("POWERFARM_HOME", "."))
        try:
            created, _ = accept_delivery(
                dict(self.headers.items()),
                body,
                os.environ.get("GITHUB_WEBHOOK_SECRET", ""),
                home / "inbox" / "github",
            )
        except WebhookError as error:
            self._send(error.status, {"error": str(error)})
            return
        self._send(202, {"accepted": created, "duplicate": not created})

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
    bind_host = os.environ.get("POWERFARM_BIND_HOST", "127.0.0.1")
    bind_port = int(os.environ.get("POWERFARM_PORT", "8000"))
    HTTPServer((bind_host, bind_port), Handler).serve_forever()
