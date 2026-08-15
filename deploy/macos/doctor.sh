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

check() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    printf 'ok   %s\n' "$name"
  else
    printf 'fail %s\n' "$name"
    return 1
  fi
}

status=0
check "python" "$POWERFARM_PYTHON" --version || status=1
check "launchctl" command -v launchctl || status=1
check "psql" command -v psql || status=1
check "cloudflared" command -v cloudflared || status=1
check "gh" command -v gh || status=1
if [ -d "$POWERFARM_HOME" ]; then
  printf 'ok   POWERFARM_HOME %s\n' "$POWERFARM_HOME"
else
  printf 'fail POWERFARM_HOME %s\n' "$POWERFARM_HOME"
  status=1
fi
[ -f "$PF_WORKER_PLIST" ] && printf 'ok   worker plist\n' || printf 'warn worker plist not installed\n'
[ -f "$PF_TUNNEL_PLIST" ] && printf 'ok   tunnel plist\n' || printf 'warn tunnel plist not installed\n'
[ -f "$PF_UPDATER_PLIST" ] && printf 'ok   updater plist\n' || printf 'warn updater plist not installed\n'
[ -f "$PF_CLOUDFLARED_CONFIG" ] && printf 'ok   cloudflared config\n' || printf 'warn cloudflared config not installed\n'

exit "$status"
