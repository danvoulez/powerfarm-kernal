#!/usr/bin/env python3
"""Upload an immutable release package to its content-addressed Storage path."""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def main() -> int:
    supabase_url, bucket, package_name, package_hash, version = sys.argv[1:]
    key = os.environ.get("SUPABASE_SECRET_KEY", "")
    if not key:
        raise RuntimeError("SUPABASE_SECRET_KEY is missing")
    package = Path(package_name)
    object_path = f"packages/{version}/{package_hash}.tar.gz"
    encoded_path = "/".join(urllib.parse.quote(part, safe="") for part in object_path.split("/"))
    url = f"{supabase_url.rstrip('/')}/storage/v1/object/{urllib.parse.quote(bucket, safe='')}/{encoded_path}"
    request = urllib.request.Request(
        url,
        data=package.read_bytes(),
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/gzip",
            "x-upsert": "true",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:1000]
        raise RuntimeError(f"Supabase Storage upload returned {error.code}: {detail}") from error
    print(f"powerfarm: uploaded package to {bucket}/{object_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
