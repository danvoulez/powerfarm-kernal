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
ensure_supabase_storage
configure_identity_services
mirror_update_package
activate_release
write_worker_runner
write_worker_plist
launchd_load_worker
ensure_cloudflare_tunnel
write_cloudflared_config
write_tunnel_plist
launchd_load_tunnel
write_updater_runner
write_updater_plist
launchd_load_updater
write_receipt update

log "update converged for version $PF_VERSION"
