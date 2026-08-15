#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$SCRIPT_DIR/lib/common.sh"

if ! pf_parse_common_args "$@"; then
  usage_common
  exit 0
fi

load_env

url="http://localhost:${POWERFARM_PORT}/health"
body="$(curl -fsS "$url")"
printf '%s\n' "$body"
printf '%s' "$body" | "$PF_VENV/bin/python" -c 'import json,sys; doc=json.load(sys.stdin); raise SystemExit(0 if doc.get("status") == "ok" else 1)'
log "local smoke passed"

if command -v cloudflared >/dev/null 2>&1 && [ -f "$PF_CLOUDFLARED_CONFIG" ]; then
  cloudflared tunnel --config "$PF_CLOUDFLARED_CONFIG" ingress validate
  cloudflared tunnel --config "$PF_CLOUDFLARED_CONFIG" ingress rule "https://$POWERFARM_API_HOSTNAME" >/dev/null
  log "cloudflared ingress smoke passed"
fi
