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
secret_key="$(pf_secret_or_keychain SUPABASE_SECRET_KEY supabase-secret-key || true)"
if [ "$PF_DRY_RUN" = "1" ]; then
  log "would converge OAuth clients from supabase/oauth-clients.json"
  exit 0
fi
[ -n "$secret_key" ] || die "SUPABASE_SECRET_KEY is required in env or macOS Keychain"

SUPABASE_SECRET_KEY="$secret_key" "$PF_PYTHON_BIN" \
  "$SCRIPT_DIR/lib/ensure_oauth_clients.py" \
  "$PF_REPO_ROOT/supabase/oauth-clients.json" "$SUPABASE_PROJECT_REF"
unset secret_key
