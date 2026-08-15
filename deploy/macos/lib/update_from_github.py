#!/usr/bin/env python3
"""Pull, verify, stage, and invoke a published Powerfarm release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Any


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"Accept": "application/octet-stream"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.removeprefix("v").split("."))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--current-version", required=True)
    parser.add_argument("--releases-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--env", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        print(
            "powerfarm: would query the latest stable GitHub Release, verify its "
            "checksum and attestation, then converge the installation"
        )
        return 0

    release = fetch_json(f"https://api.github.com/repos/{args.repository}/releases/latest")
    version = release["tag_name"].removeprefix("v")
    if version_tuple(version) <= version_tuple(args.current_version):
        print(f"powerfarm: release {args.current_version} is current")
        return 0
    assets = {asset["name"]: asset["browser_download_url"] for asset in release["assets"]}
    archive_name = f"powerfarm-{version}-macos-arm64.tar.gz"
    checksum_name = archive_name + ".sha256"
    if archive_name not in assets or checksum_name not in assets:
        raise RuntimeError(f"release v{version} is missing its macOS package or checksum")
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    archive_path = args.cache_dir / archive_name
    checksum_path = args.cache_dir / checksum_name
    download(assets[archive_name], archive_path)
    download(assets[checksum_name], checksum_path)
    expected = checksum_path.read_text().split()[0]
    actual = digest(archive_path)
    if actual != expected:
        raise RuntimeError("release package checksum mismatch")
    subprocess.run(
        ["gh", "attestation", "verify", str(archive_path), "-R", args.repository], check=True
    )

    destination = args.releases_dir / version
    if not destination.exists():
        with tempfile.TemporaryDirectory(dir=args.releases_dir) as temporary:
            with tarfile.open(archive_path, "r:gz") as archive:
                archive.extractall(temporary, filter="data")
            extracted = Path(temporary) / f"powerfarm-{version}"
            if not extracted.is_dir():
                raise RuntimeError("release package has an unexpected root directory")
            os.replace(extracted, destination)
    update = destination / "deploy" / "macos" / "update.sh"
    env = os.environ.copy()
    env["POWERFARM_PACKAGE_PATH"] = str(archive_path)
    env["POWERFARM_PACKAGE_HASH"] = actual
    subprocess.run([str(update), "--env", str(args.env)], check=True, env=env)
    print(f"powerfarm: activated release {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
