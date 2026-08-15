#!/usr/bin/env python3
"""Converge hosted Supabase Auth configuration from config.toml."""

from __future__ import annotations

import json
import os
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def request(url: str, token: str, method: str = "GET", body: dict[str, Any] | None = None) -> Any:
    payload = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, data=payload, headers=headers, method=method), timeout=30
        ) as response:
            content = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:1000]
        raise RuntimeError(f"Supabase Management API returned {error.code}: {detail}") from error
    return json.loads(content) if content else None


def desired_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as config_file:
        config = tomllib.load(config_file)
    auth = config["auth"]
    passkey = auth["passkey"]
    webauthn = auth["webauthn"]
    oauth = auth["oauth_server"]
    return {
        "site_url": auth["site_url"],
        "uri_allow_list": ",".join(auth.get("additional_redirect_urls", [])),
        "passkey_enabled": bool(passkey["enabled"]),
        "webauthn_rp_display_name": webauthn["rp_display_name"],
        "webauthn_rp_id": webauthn["rp_id"],
        "webauthn_rp_origins": ",".join(webauthn["rp_origins"]),
        "oauth_server_enabled": bool(oauth["enabled"]),
        "oauth_server_allow_dynamic_registration": bool(oauth["allow_dynamic_registration"]),
        "oauth_server_authorization_path": oauth["authorization_url_path"],
    }


def normalized(value: Any) -> Any:
    if isinstance(value, str) and "," in value:
        return ",".join(sorted(part.strip() for part in value.split(",") if part.strip()))
    return value


def main() -> int:
    config_path = Path(sys.argv[1])
    project_ref = sys.argv[2]
    token = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError("SUPABASE_ACCESS_TOKEN is missing")
    url = f"https://api.supabase.com/v1/projects/{project_ref}/config/auth"
    desired = desired_config(config_path)
    current = request(url, token)
    changes = {
        key: value
        for key, value in desired.items()
        if normalized(current.get(key)) != normalized(value)
    }
    if changes:
        request(url, token, method="PATCH", body=changes)
        print("powerfarm: updated Supabase Auth fields: " + ", ".join(sorted(changes)))
    else:
        print("powerfarm: Supabase Auth configuration already converged")
    verified = request(url, token)
    mismatches = [
        key for key, value in desired.items() if normalized(verified.get(key)) != normalized(value)
    ]
    if mismatches:
        raise RuntimeError("Supabase Auth verification failed for: " + ", ".join(mismatches))
    print("powerfarm: Supabase Auth verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
