#!/usr/bin/env python3
"""Run the one-time GitHub App Manifest consent and store its credentials."""

from __future__ import annotations

import html
import json
import os
import secrets
import subprocess
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HOST = "127.0.0.1"
PORT = 8765
ACCOUNT = "powerfarm"


def keychain_set(service: str, value: str) -> None:
    subprocess.run(
        [
            "security",
            "add-generic-password",
            "-U",
            "-a",
            ACCOUNT,
            "-s",
            service,
            "-w",
            value,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def convert_manifest(code: str) -> dict[str, Any]:
    result = subprocess.run(
        ["gh", "api", "--method", "POST", f"/app-manifests/{code}/conversions"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    manifest_path = Path(sys.argv[1])
    manifest = json.loads(manifest_path.read_text())
    state = secrets.token_urlsafe(32)
    manifest["redirect_url"] = f"http://{HOST}:{PORT}/callback"
    captured: dict[str, str] = {}
    completed = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/start":
                value = html.escape(json.dumps(manifest, separators=(",", ":")), quote=True)
                action = f"https://github.com/settings/apps/new?state={urllib.parse.quote(state)}"
                page = f"""<!doctype html><meta charset=utf-8>
<title>Register Powerfarm GitHub App</title>
<form id=register method=post action=\"{action}\">
<input type=hidden name=manifest value=\"{value}\">
</form>
<p>Redirecting to GitHub for the one-time app registration...</p>
<script>document.getElementById('register').submit()</script>"""
                self._send(200, page)
                return
            if parsed.path == "/callback":
                query = urllib.parse.parse_qs(parsed.query)
                if query.get("state", [""])[0] != state:
                    self._send(400, "Invalid state. Close this window and retry.")
                    completed.set()
                    return
                code = query.get("code", [""])[0]
                if not code:
                    self._send(400, "Missing manifest code. Close this window and retry.")
                    completed.set()
                    return
                captured["code"] = code
                self._send(200, "GitHub App approved. Return to the terminal.")
                completed.set()
                return
            self._send(404, "Not found")

        def _send(self, status: int, body: str) -> None:
            payload = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.timeout = 1
    print("powerfarm: opening GitHub for one-time app registration")
    webbrowser.open(f"http://{HOST}:{PORT}/start")
    for _ in range(600):
        server.handle_request()
        if completed.is_set():
            break
    server.server_close()
    code = captured.get("code")
    if not code:
        raise RuntimeError("GitHub App registration timed out or was denied")

    app = convert_manifest(code)
    home = Path(os.environ["POWERFARM_HOME"])
    secrets_dir = home / "secrets"
    state_dir = home / "state"
    secrets_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    pem_path = secrets_dir / "github-app.pem"
    pem_path.write_text(app["pem"])
    pem_path.chmod(0o600)

    keychain_set("powerfarm.github.app-id", str(app["id"]))
    keychain_set("powerfarm.github.client-id", app["client_id"])
    keychain_set("powerfarm.github.client-secret", app["client_secret"])
    keychain_set("powerfarm.github.webhook-secret", app["webhook_secret"])

    public_state = {
        "app_id": app["id"],
        "client_id": app["client_id"],
        "name": app["name"],
        "slug": app["slug"],
        "pem_path": str(pem_path),
    }
    state_path = state_dir / "github-app.json"
    state_path.write_text(json.dumps(public_state, indent=2, sort_keys=True) + "\n")
    state_path.chmod(0o600)
    install_url = f"https://github.com/apps/{app['slug']}/installations/new"
    print(f"powerfarm: GitHub App registered as {app['slug']}")
    print(f"powerfarm: credentials stored in Keychain; private key: {pem_path}")
    print(f"powerfarm: complete the one-time repository installation: {install_url}")
    webbrowser.open(install_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
