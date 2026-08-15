#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=lib/keychain.sh
. "$SCRIPT_DIR/lib/keychain.sh"

if ! pf_parse_common_args "$@"; then
  usage_common
  exit 0
fi

load_env
resolve_python
require_env_value SUPABASE_PROJECT_REF

access_token="$(pf_secret_or_keychain SUPABASE_ACCESS_TOKEN supabase-access-token || true)"
if [ "$PF_DRY_RUN" = "1" ]; then
  log "would converge Supabase Auth config for $SUPABASE_PROJECT_REF from supabase/config.toml"
  exit 0
fi
[ -n "$access_token" ] || die "SUPABASE_ACCESS_TOKEN is required in env or macOS Keychain"

SUPABASE_ACCESS_TOKEN="$access_token" "$PF_PYTHON_BIN" \
  "$SCRIPT_DIR/lib/configure_supabase_auth.py" \
  "$PF_REPO_ROOT/supabase/config.toml" "$SUPABASE_PROJECT_REF"
unset access_token
