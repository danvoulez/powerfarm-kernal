#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$SCRIPT_DIR/lib/common.sh"

if ! pf_parse_common_args "$@"; then
  usage_common
  printf '  --purge        Remove LAB runtime directory after unloading services\n'
  exit 0
fi

require_macos
load_env

launchd_unload_updater
launchd_unload_tunnel
launchd_unload_worker
run rm -f "$PF_WORKER_PLIST"
run rm -f "$PF_TUNNEL_PLIST"
run rm -f "$PF_UPDATER_PLIST"
run rm -f "$PF_CLOUDFLARED_CONFIG"
run rm -f "$PF_WORKER_RUNNER"
run rm -f "$PF_UPDATER_RUNNER"

if [ "$PF_PURGE" = "1" ]; then
  run rm -rf "$POWERFARM_HOME"
else
  ensure_dirs
  write_receipt uninstall
  log "kept LAB data at $POWERFARM_HOME; pass --purge to remove it"
fi

log "uninstall converged"
