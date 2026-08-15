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
ensure_dirs
write_installed_env
install_python_env
apply_supabase_migrations
write_worker_runner
write_worker_plist
launchd_load_worker
ensure_cloudflare_tunnel
write_cloudflared_config
write_tunnel_plist
launchd_load_tunnel
write_receipt install

log "install converged for $POWERFARM_API_HOSTNAME"
