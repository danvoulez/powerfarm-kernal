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
command -v gh >/dev/null 2>&1 || die "gh CLI not found"
command -v security >/dev/null 2>&1 || die "macOS security CLI not found"

if [ "$PF_DRY_RUN" = "1" ]; then
  log "would open the one-time GitHub App manifest consent flow"
  log "would store credentials in Keychain and the private key under $POWERFARM_HOME/secrets"
  exit 0
fi

mkdir -p "$POWERFARM_HOME/secrets"
chmod 700 "$POWERFARM_HOME/secrets"
POWERFARM_HOME="$POWERFARM_HOME" "$PF_PYTHON_BIN" \
  "$SCRIPT_DIR/github-app/register.py" \
  "$SCRIPT_DIR/github-app/manifest.json"
