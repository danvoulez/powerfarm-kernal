#!/usr/bin/env python3
"""Idempotently create or update declared Supabase OAuth clients."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def request(url: str, key: str, method: str = "GET", body: dict[str, Any] | None = None) -> Any:
    payload = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, data=payload, headers=headers, method=method), timeout=30
        ) as response:
            content = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:1000]
        raise RuntimeError(f"Supabase Auth API returned {error.code}: {detail}") from error
    return json.loads(content) if content else None


def comparable(client: dict[str, Any]) -> dict[str, Any]:
    keys = ("client_name", "client_uri", "redirect_uris", "client_type", "token_endpoint_auth_method")
    result = {key: client.get(key) for key in keys}
    result["redirect_uris"] = sorted(result.get("redirect_uris") or [])
    return result


def main() -> int:
    declaration = json.loads(Path(sys.argv[1]).read_text())
    project_ref = sys.argv[2]
    secret_key = os.environ.get("SUPABASE_SECRET_KEY", "")
    if not secret_key:
        raise RuntimeError("SUPABASE_SECRET_KEY is missing")
    url = f"https://{project_ref}.supabase.co/auth/v1/admin/oauth/clients"
    response = request(url, secret_key)
    if isinstance(response, dict):
        existing = response.get("clients", [])
    elif isinstance(response, list):
        existing = response
    else:
        existing = []
    by_name: dict[str, list[dict[str, Any]]] = {}
    for client in existing:
        by_name.setdefault(client.get("client_name") or client.get("name"), []).append(client)

    for desired in declaration.get("clients", []):
        matches = by_name.get(desired["client_name"], [])
        if len(matches) > 1:
            raise RuntimeError(f"duplicate remote OAuth clients named {desired['client_name']!r}")
        if not matches:
            created = request(url, secret_key, method="POST", body=desired)
            print(f"powerfarm: created OAuth client {desired['client_name']} ({created['client_id']})")
            continue
        current = matches[0]
        if comparable(current) == comparable(desired):
            print(f"powerfarm: OAuth client already converged: {desired['client_name']}")
            continue
        client_id = current.get("client_id") or current.get("id")
        request(f"{url}/{client_id}", secret_key, method="PUT", body=desired)
        print(f"powerfarm: updated OAuth client {desired['client_name']} ({client_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
