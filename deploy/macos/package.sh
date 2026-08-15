#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$SCRIPT_DIR/VERSION")"
OUTPUT_DIR="$REPO_ROOT/dist"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output)
      [ "$#" -ge 2 ] || { printf '%s\n' '--output requires a path' >&2; exit 2; }
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -h|--help)
      printf 'Usage: package.sh [--output DIR]\n'
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

command -v uv >/dev/null 2>&1 || { printf '%s\n' 'uv is required' >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/powerfarm-package.XXXXXX")"
trap 'rm -rf "$BUILD_DIR"' EXIT
mkdir -p "$BUILD_DIR/wheelhouse"
SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git -C "$REPO_ROOT" show -s --format=%ct HEAD)}"
export SOURCE_DATE_EPOCH

uv build --wheel --out-dir "$BUILD_DIR/wheelhouse" "$REPO_ROOT"
uv export --locked --no-dev --no-emit-project --output-file "$BUILD_DIR/requirements.txt"
uv run --with pip python -m pip download --quiet --dest "$BUILD_DIR/wheelhouse" \
  --require-hashes --only-binary=:all: --platform macosx_11_0_arm64 \
  --python-version 312 --requirement "$BUILD_DIR/requirements.txt"

uv run python "$REPO_ROOT/scripts/release/build_package.py" \
  "$REPO_ROOT" "$BUILD_DIR/wheelhouse" "$OUTPUT_DIR" "$VERSION"
