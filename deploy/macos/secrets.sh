#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/keychain.sh
. "$SCRIPT_DIR/lib/keychain.sh"

usage() {
  cat <<'EOF'
Usage:
  secrets.sh set NAME
  secrets.sh has NAME
  secrets.sh delete NAME

Names:
  supabase-access-token
  supabase-secret-key
  github-app-id
  github-client-id
  github-client-secret
  github-webhook-secret
EOF
}

[ "$#" -eq 2 ] || { usage; exit 2; }
action="$1"
name="$2"
pf_keychain_service "$name" >/dev/null || { printf 'unknown secret: %s\n' "$name" >&2; exit 2; }

case "$action" in
  set)
    IFS= read -r -s -p "Value for $name: " value
    printf '\n'
    [ -n "$value" ] || { printf 'empty value rejected\n' >&2; exit 1; }
    pf_keychain_set "$name" "$value"
    unset value
    printf 'stored %s in macOS Keychain\n' "$name"
    ;;
  has)
    if pf_keychain_get "$name" >/dev/null; then
      printf 'present %s\n' "$name"
    else
      printf 'missing %s\n' "$name"
      exit 1
    fi
    ;;
  delete)
    pf_keychain_delete "$name"
    printf 'deleted %s\n' "$name"
    ;;
  *)
    usage
    exit 2
    ;;
esac
