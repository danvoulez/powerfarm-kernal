#!/usr/bin/env python3
"""Build the deterministic Powerfarm macOS package and its manifest."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

INCLUDE = (
    "agent",
    "conformance",
    "deploy",
    "genesis",
    "kernel",
    "supabase",
    "worker",
    "README.md",
    "Powerfarm Implementation Plan 2.md",
    "Powerfarm System Specification v3.md",
    "pyproject.toml",
    "uv.lock",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def included_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for name in INCLUDE:
        path = root / name
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                item
                for item in path.rglob("*")
                if item.is_file()
                and "__pycache__" not in item.parts
                and ".temp" not in item.parts
                and item.name != ".DS_Store"
                and not item.name.endswith((".pyc", ".pyo"))
            )
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def add_file(archive: tarfile.TarFile, source: Path, destination: str, epoch: int) -> None:
    info = archive.gettarinfo(str(source), arcname=destination)
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    info.mtime = epoch
    executable = source.suffix == ".sh" or (
        source.suffix == ".py"
        and any(part in {"deploy", "scripts"} for part in source.parts)
    )
    info.mode = 0o755 if executable else 0o644
    with source.open("rb") as content:
        archive.addfile(info, content)


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    wheelhouse = Path(sys.argv[2]).resolve()
    output = Path(sys.argv[3]).resolve()
    version = sys.argv[4]
    epoch = int(os.environ["SOURCE_DATE_EPOCH"])
    commit = subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()
    package_root = f"powerfarm-{version}"
    files = included_files(root)
    migrations = [
        {
            "name": path.name,
            "sha256": digest(path),
            "version": path.name.split("_", 1)[0],
        }
        for path in files
        if path.parent.name == "migrations" and path.suffix == ".sql"
    ]
    manifest = {
        "format": "powerfarm-package-v1",
        "git_commit": commit,
        "migrations": migrations,
        "platform": "macos-arm64",
        "source_date_epoch": epoch,
        "version": version,
    }
    manifest_bytes = json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode() + b"\n"
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / f"powerfarm-{version}-macos-arm64.tar.gz"

    with tempfile.TemporaryDirectory() as temporary:
        raw_path = Path(temporary) / "package.tar.gz"
        with (
            raw_path.open("wb") as raw,
            gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed,
            tarfile.open(fileobj=compressed, mode="w") as archive,
        ):
            for path in files:
                relative = path.relative_to(root).as_posix()
                add_file(archive, path, f"{package_root}/{relative}", epoch)
            for path in sorted(wheelhouse.glob("*"), key=lambda item: item.name):
                if path.is_file():
                    add_file(archive, path, f"{package_root}/wheelhouse/{path.name}", epoch)
            info = tarfile.TarInfo(f"{package_root}/package-manifest.jcs.json")
            info.size = len(manifest_bytes)
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            info.mtime = epoch
            archive.addfile(info, io.BytesIO(manifest_bytes))
        archive_path.write_bytes(raw_path.read_bytes())

    checksum = digest(archive_path)
    archive_path.with_suffix(archive_path.suffix + ".sha256").write_text(
        f"{checksum}  {archive_path.name}\n"
    )
    (output / f"powerfarm-{version}-package-manifest.jcs.json").write_bytes(manifest_bytes)
    print(archive_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
