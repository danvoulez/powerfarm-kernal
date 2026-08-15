#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$SCRIPT_DIR/lib/common.sh"

if ! pf_parse_common_args "$@"; then
  usage_common
  exit 0
fi

require_macos
load_env
resolve_python
ensure_dirs

lock="$PF_STATE_DIR/update.lock"
if [ "$PF_DRY_RUN" != "1" ]; then
  if ! mkdir "$lock" 2>/dev/null; then
    log "another update check is running"
    exit 0
  fi
  trap 'rmdir "$lock"' EXIT
fi

args=(
  "$PF_SCRIPT_DIR/lib/update_from_github.py"
  --repository "$POWERFARM_GITHUB_REPOSITORY"
  --current-version "$PF_VERSION"
  --releases-dir "$PF_RELEASES_DIR"
  --cache-dir "$PF_CACHE_DIR"
  --env "$PF_ENV_INSTALLED"
)
if [ "$PF_DRY_RUN" = "1" ]; then
  args+=(--dry-run)
fi
"$PF_PYTHON_BIN" "${args[@]}"
