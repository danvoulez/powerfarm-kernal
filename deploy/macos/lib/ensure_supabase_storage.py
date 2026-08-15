#!/usr/bin/env python3
"""Create or converge private Supabase Storage buckets through the API."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def request(url: str, key: str, method: str = "GET", body: dict[str, Any] | None = None) -> Any:
    payload = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, data=payload, headers=headers, method=method), timeout=30
        ) as response:
            content = response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        detail = error.read().decode(errors="replace")[:1000]
        raise RuntimeError(f"Supabase Storage API returned {error.code}: {detail}") from error
    return json.loads(content) if content else None


def main() -> int:
    base_url = sys.argv[1].rstrip("/") + "/storage/v1/bucket"
    buckets = sys.argv[2:]
    key = os.environ.get("SUPABASE_SECRET_KEY", "")
    if not key:
        raise RuntimeError("SUPABASE_SECRET_KEY is missing")
    for bucket in buckets:
        current = request(f"{base_url}/{urllib.parse.quote(bucket, safe='')}", key)
        desired = {"id": bucket, "name": bucket, "public": False}
        if current is None:
            request(base_url, key, method="POST", body=desired)
            print(f"powerfarm: created private Storage bucket {bucket}")
        elif current.get("public"):
            request(
                f"{base_url}/{urllib.parse.quote(bucket, safe='')}",
                key,
                method="PUT",
                body={"public": False},
            )
            print(f"powerfarm: made Storage bucket private: {bucket}")
        else:
            print(f"powerfarm: Storage bucket already converged: {bucket}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
