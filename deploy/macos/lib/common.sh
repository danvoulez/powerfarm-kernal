#!/usr/bin/env bash
set -euo pipefail

PF_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PF_REPO_ROOT="$(cd "$PF_SCRIPT_DIR/../.." && pwd)"
PF_VERSION="$(tr -d '[:space:]' < "$PF_SCRIPT_DIR/VERSION")"

PF_LABEL_WORKER="com.powerfarm.worker"
PF_LABEL_TUNNEL="com.powerfarm.tunnel"
PF_DEFAULT_ENV="$PF_SCRIPT_DIR/powerfarm.env"

log() {
  printf 'powerfarm: %s\n' "$*"
}

die() {
  printf 'powerfarm: ERROR: %s\n' "$*" >&2
  exit 1
}

usage_common() {
  cat <<EOF
Common options:
  --env PATH      Environment file. Default: $PF_DEFAULT_ENV
  --dry-run       Print actions without changing local state
EOF
}

pf_parse_common_args() {
  PF_ENV_FILE="$PF_DEFAULT_ENV"
  PF_DRY_RUN=0
  PF_PURGE=0
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --env)
        [ "$#" -ge 2 ] || die "--env requires a path"
        PF_ENV_FILE="$2"
        shift 2
        ;;
      --dry-run)
        PF_DRY_RUN=1
        shift
        ;;
      --purge)
        PF_PURGE=1
        shift
        ;;
      -h|--help)
        return 2
        ;;
      *)
        die "unknown argument: $1"
        ;;
    esac
  done
}

run() {
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    printf '+'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

require_macos() {
  [ "$(uname -s)" = "Darwin" ] || die "this pack targets macOS launchd only"
  command -v launchctl >/dev/null 2>&1 || die "launchctl not found"
}

load_env() {
  [ -f "$PF_ENV_FILE" ] || die "env file not found: $PF_ENV_FILE; copy deploy/macos/powerfarm.env.example first"
  set -a
  # shellcheck disable=SC1090
  . "$PF_ENV_FILE"
  set +a

  POWERFARM_HOME="${POWERFARM_HOME:-/Volumes/LAB-8/powerfarm}"
  POWERFARM_DOMAIN="${POWERFARM_DOMAIN:-powerfarm.app}"
  POWERFARM_API_HOSTNAME="${POWERFARM_API_HOSTNAME:-api.$POWERFARM_DOMAIN}"
  POWERFARM_APP_HOSTNAME="${POWERFARM_APP_HOSTNAME:-app.$POWERFARM_DOMAIN}"
  POWERFARM_PORT="${POWERFARM_PORT:-8000}"
  POWERFARM_PYTHON="${POWERFARM_PYTHON:-python3.12}"
  CLOUDFLARE_TUNNEL_NAME="${CLOUDFLARE_TUNNEL_NAME:-powerfarm-lab}"
  CLOUDFLARE_HOME="${CLOUDFLARE_HOME:-$HOME/.cloudflared}"

  PF_STATE_DIR="$POWERFARM_HOME/state"
  PF_LOG_DIR="$POWERFARM_HOME/logs"
  PF_RUN_DIR="$POWERFARM_HOME/run"
  PF_VENV="$POWERFARM_HOME/venv"
  PF_RECEIPTS_DIR="$POWERFARM_HOME/receipts"
  PF_ENV_INSTALLED="$POWERFARM_HOME/powerfarm.env"
  PF_WORKER_RUNNER="$PF_RUN_DIR/pf-worker"
  PF_WORKER_PLIST="$HOME/Library/LaunchAgents/$PF_LABEL_WORKER.plist"
  PF_TUNNEL_PLIST="$HOME/Library/LaunchAgents/$PF_LABEL_TUNNEL.plist"
  PF_CLOUDFLARED_CONFIG="$CLOUDFLARE_HOME/powerfarm-lab.yml"
}

require_env_value() {
  local name="$1"
  local value="${!name:-}"
  [ -n "$value" ] || die "$name is required in $PF_ENV_FILE"
}

ensure_dirs() {
  run mkdir -p "$POWERFARM_HOME" "$PF_STATE_DIR" "$PF_LOG_DIR" "$PF_RUN_DIR" "$PF_RECEIPTS_DIR" "$HOME/Library/LaunchAgents" "$CLOUDFLARE_HOME"
  if [ "${PF_DRY_RUN:-0}" != "1" ]; then
    chmod 700 "$POWERFARM_HOME" "$PF_STATE_DIR" "$PF_RUN_DIR" "$PF_RECEIPTS_DIR"
  fi
}

resolve_python() {
  if command -v "$POWERFARM_PYTHON" >/dev/null 2>&1; then
    PF_PYTHON_BIN="$(command -v "$POWERFARM_PYTHON")"
  elif command -v python3 >/dev/null 2>&1; then
    PF_PYTHON_BIN="$(command -v python3)"
  else
    die "Python 3.12+ not found"
  fi
  "$PF_PYTHON_BIN" - <<'PY' || die "Python 3.12+ is required"
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
}

install_python_env() {
  resolve_python
  if [ ! -x "$PF_VENV/bin/python" ]; then
    if command -v uv >/dev/null 2>&1; then
      run uv venv --python "$PF_PYTHON_BIN" "$PF_VENV"
    else
      run "$PF_PYTHON_BIN" -m venv "$PF_VENV"
    fi
  fi
  if command -v uv >/dev/null 2>&1; then
    run uv pip install --python "$PF_VENV/bin/python" "$PF_REPO_ROOT"
  else
    run "$PF_VENV/bin/python" -m pip install --upgrade pip
    run "$PF_VENV/bin/python" -m pip install "$PF_REPO_ROOT"
  fi
}

compute_genesis_root() {
  "$PF_VENV/bin/python" -m genesis.ceremony | "$PF_VENV/bin/python" -c 'import json,sys; print(json.load(sys.stdin)["genesis_root_hash"])'
}

write_installed_env() {
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would write $PF_ENV_INSTALLED"
    return
  fi
  cp "$PF_ENV_FILE" "$PF_ENV_INSTALLED"
  chmod 600 "$PF_ENV_INSTALLED"
}

write_worker_runner() {
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would write $PF_WORKER_RUNNER"
    return
  fi
  local genesis_root
  genesis_root="$(compute_genesis_root)"
  cat > "$PF_WORKER_RUNNER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
set -a
. "$PF_ENV_INSTALLED"
set +a
export POWERFARM_HOME="$POWERFARM_HOME"
export POWERFARM_GENESIS_ROOT="$genesis_root"
cd "$PF_REPO_ROOT"
exec "$PF_VENV/bin/python" -m worker.serve
EOF
  chmod 700 "$PF_WORKER_RUNNER"
}

write_worker_plist() {
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would write $PF_WORKER_PLIST"
    return
  fi
  cat > "$PF_WORKER_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$PF_LABEL_WORKER</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PF_WORKER_RUNNER</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$PF_REPO_ROOT</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$PF_LOG_DIR/worker.out.log</string>
  <key>StandardErrorPath</key>
  <string>$PF_LOG_DIR/worker.err.log</string>
</dict>
</plist>
EOF
  plutil -lint "$PF_WORKER_PLIST" >/dev/null
}

launchd_load_worker() {
  local domain="gui/$(id -u)"
  if launchctl print "$domain/$PF_LABEL_WORKER" >/dev/null 2>&1; then
    run launchctl bootout "$domain" "$PF_WORKER_PLIST"
  fi
  run launchctl bootstrap "$domain" "$PF_WORKER_PLIST"
  run launchctl kickstart -k "$domain/$PF_LABEL_WORKER"
}

launchd_unload_worker() {
  local domain="gui/$(id -u)"
  if launchctl print "$domain/$PF_LABEL_WORKER" >/dev/null 2>&1; then
    run launchctl bootout "$domain" "$PF_WORKER_PLIST"
  fi
}

write_tunnel_plist() {
  local cloudflared_bin
  cloudflared_bin="$(command -v cloudflared)"
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would write $PF_TUNNEL_PLIST"
    return
  fi
  cat > "$PF_TUNNEL_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$PF_LABEL_TUNNEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$cloudflared_bin</string>
    <string>tunnel</string>
    <string>--config</string>
    <string>$PF_CLOUDFLARED_CONFIG</string>
    <string>run</string>
    <string>$PF_TUNNEL_ID</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$PF_LOG_DIR/tunnel.out.log</string>
  <key>StandardErrorPath</key>
  <string>$PF_LOG_DIR/tunnel.err.log</string>
</dict>
</plist>
EOF
  plutil -lint "$PF_TUNNEL_PLIST" >/dev/null
}

launchd_load_tunnel() {
  local domain="gui/$(id -u)"
  if launchctl print "$domain/$PF_LABEL_TUNNEL" >/dev/null 2>&1; then
    run launchctl bootout "$domain" "$PF_TUNNEL_PLIST"
  fi
  run launchctl bootstrap "$domain" "$PF_TUNNEL_PLIST"
  run launchctl kickstart -k "$domain/$PF_LABEL_TUNNEL"
}

launchd_unload_tunnel() {
  local domain="gui/$(id -u)"
  if launchctl print "$domain/$PF_LABEL_TUNNEL" >/dev/null 2>&1; then
    run launchctl bootout "$domain" "$PF_TUNNEL_PLIST"
  fi
}

apply_supabase_migrations() {
  if [ "${PF_DRY_RUN:-0}" = "1" ] && [ -z "${DATABASE_URL:-}" ]; then
    log "would require DATABASE_URL for Supabase migrations"
  else
    require_env_value DATABASE_URL
  fi
  if [ "${PF_DRY_RUN:-0}" != "1" ]; then
    command -v psql >/dev/null 2>&1 || die "psql not found; install libpq/postgresql client tools"
  fi
  local db_url="${DATABASE_URL:-<DATABASE_URL>}"
  local migration
  for migration in "$PF_REPO_ROOT"/supabase/migrations/*.sql; do
    [ -f "$migration" ] || continue
    log "applying Supabase migration $(basename "$migration")"
    run psql "$db_url" -v ON_ERROR_STOP=1 -f "$migration"
  done
}

tunnel_id_from_list() {
  cloudflared tunnel list --output json 2>/dev/null | "$PF_PYTHON_BIN" -c '
import json, sys
name = sys.argv[1]
try:
    tunnels = json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
for tunnel in tunnels:
    if tunnel.get("name") == name:
        print(tunnel.get("id") or tunnel.get("uuid") or "")
        raise SystemExit(0)
raise SystemExit(1)
' "$CLOUDFLARE_TUNNEL_NAME"
}

ensure_cloudflare_tunnel() {
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    PF_TUNNEL_ID="${CLOUDFLARE_TUNNEL_ID:-dry-run-tunnel-id}"
    PF_TUNNEL_CREDENTIALS="${CLOUDFLARE_CREDENTIALS_FILE:-$CLOUDFLARE_HOME/$PF_TUNNEL_ID.json}"
    log "would ensure Cloudflare tunnel $CLOUDFLARE_TUNNEL_NAME and DNS for $POWERFARM_API_HOSTNAME"
    return
  fi
  command -v cloudflared >/dev/null 2>&1 || die "cloudflared not found; install it and run cloudflared tunnel login"
  local tunnel_id="${CLOUDFLARE_TUNNEL_ID:-}"
  if [ -z "$tunnel_id" ]; then
    tunnel_id="$(tunnel_id_from_list || true)"
  fi
  if [ -z "$tunnel_id" ]; then
    log "creating Cloudflare tunnel $CLOUDFLARE_TUNNEL_NAME"
    run cloudflared tunnel create "$CLOUDFLARE_TUNNEL_NAME"
    tunnel_id="$(tunnel_id_from_list || true)"
  fi
  [ -n "$tunnel_id" ] || die "could not resolve Cloudflare tunnel id for $CLOUDFLARE_TUNNEL_NAME"
  PF_TUNNEL_ID="$tunnel_id"
  PF_TUNNEL_CREDENTIALS="${CLOUDFLARE_CREDENTIALS_FILE:-$CLOUDFLARE_HOME/$PF_TUNNEL_ID.json}"
  [ -f "$PF_TUNNEL_CREDENTIALS" ] || die "Cloudflare tunnel credentials not found: $PF_TUNNEL_CREDENTIALS"

  run cloudflared tunnel route dns --overwrite-dns "$PF_TUNNEL_ID" "$POWERFARM_API_HOSTNAME"
  if [ -n "${POWERFARM_APP_HOSTNAME:-}" ]; then
    run cloudflared tunnel route dns --overwrite-dns "$PF_TUNNEL_ID" "$POWERFARM_APP_HOSTNAME"
  fi
}

write_cloudflared_config() {
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would write $PF_CLOUDFLARED_CONFIG"
    return
  fi
  cat > "$PF_CLOUDFLARED_CONFIG" <<EOF
tunnel: $PF_TUNNEL_ID
credentials-file: $PF_TUNNEL_CREDENTIALS

ingress:
  - hostname: $POWERFARM_API_HOSTNAME
    service: http://localhost:$POWERFARM_PORT
  - hostname: $POWERFARM_APP_HOSTNAME
    service: http://localhost:$POWERFARM_PORT
  - service: http_status:404
EOF
  cloudflared tunnel --config "$PF_CLOUDFLARED_CONFIG" ingress validate
}

write_receipt() {
  local action="$1"
  local receipt="$PF_RECEIPTS_DIR/$(date -u +%Y%m%dT%H%M%SZ)-$action.json"
  local head
  head="$(git -C "$PF_REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would write receipt $receipt"
    return
  fi
  "$PF_PYTHON_BIN" - "$receipt" "$action" "$PF_VERSION" "$head" "$POWERFARM_HOME" "$POWERFARM_API_HOSTNAME" <<'PY'
import json, sys, time
path, action, version, commit, home, api = sys.argv[1:]
doc = {
    "action": action,
    "version": version,
    "git_commit": commit,
    "powerfarm_home": home,
    "api_hostname": api,
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
  log "receipt: $receipt"
}
