#!/usr/bin/env bash
set -euo pipefail

PF_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PF_REPO_ROOT="$(cd "$PF_SCRIPT_DIR/../.." && pwd)"
PF_VERSION="$(tr -d '[:space:]' < "$PF_SCRIPT_DIR/VERSION")"

# shellcheck source=keychain.sh
. "$PF_SCRIPT_DIR/lib/keychain.sh"

PF_LABEL_WORKER="com.powerfarm.worker"
PF_LABEL_TUNNEL="com.powerfarm.tunnel"
PF_LABEL_UPDATER="com.powerfarm.updater"
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
        # shellcheck disable=SC2034  # Consumed by uninstall.sh after sourcing this library.
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
  POWERFARM_BIND_HOST="${POWERFARM_BIND_HOST:-127.0.0.1}"
  POWERFARM_PORT="${POWERFARM_PORT:-8000}"
  POWERFARM_PYTHON="${POWERFARM_PYTHON:-python3.12}"
  CLOUDFLARE_TUNNEL_NAME="${CLOUDFLARE_TUNNEL_NAME:-powerfarm-lab}"
  CLOUDFLARE_HOME="${CLOUDFLARE_HOME:-$HOME/.cloudflared}"
  SUPABASE_URL="${SUPABASE_URL:-${SUPABASE_PROJECT_REF:+https://$SUPABASE_PROJECT_REF.supabase.co}}"
  POWERFARM_LEDGER_BUCKET="${POWERFARM_LEDGER_BUCKET:-powerfarm-ledger}"
  POWERFARM_PACKAGES_BUCKET="${POWERFARM_PACKAGES_BUCKET:-powerfarm-packages}"
  POWERFARM_GITHUB_REPOSITORY="${POWERFARM_GITHUB_REPOSITORY:-danvoulez/powerfarm-kernal}"
  POWERFARM_UPDATE_CHANNEL="${POWERFARM_UPDATE_CHANNEL:-stable}"
  POWERFARM_UPDATE_INTERVAL="${POWERFARM_UPDATE_INTERVAL:-300}"

  PF_STATE_DIR="$POWERFARM_HOME/state"
  PF_LOG_DIR="$POWERFARM_HOME/logs"
  PF_RUN_DIR="$POWERFARM_HOME/run"
  PF_VENVS_DIR="$POWERFARM_HOME/venvs"
  PF_VENV="$PF_VENVS_DIR/$PF_VERSION"
  PF_RELEASES_DIR="$POWERFARM_HOME/releases"
  PF_CACHE_DIR="$POWERFARM_HOME/cache"
  PF_INBOX_DIR="$POWERFARM_HOME/inbox"
  PF_CURRENT_LINK="$POWERFARM_HOME/current"
  PF_RECEIPTS_DIR="$POWERFARM_HOME/receipts"
  PF_ENV_INSTALLED="$POWERFARM_HOME/powerfarm.env"
  PF_WORKER_RUNNER="$PF_RUN_DIR/pf-worker"
  PF_WORKER_PLIST="$HOME/Library/LaunchAgents/$PF_LABEL_WORKER.plist"
  PF_TUNNEL_PLIST="$HOME/Library/LaunchAgents/$PF_LABEL_TUNNEL.plist"
  PF_UPDATER_RUNNER="$PF_RUN_DIR/pf-updater"
  PF_UPDATER_PLIST="$HOME/Library/LaunchAgents/$PF_LABEL_UPDATER.plist"
  PF_CLOUDFLARED_CONFIG="$CLOUDFLARE_HOME/powerfarm-lab.yml"
}

require_env_value() {
  local name="$1"
  local value="${!name:-}"
  [ -n "$value" ] || die "$name is required in $PF_ENV_FILE"
}

ensure_dirs() {
  run mkdir -p "$POWERFARM_HOME" "$PF_STATE_DIR" "$PF_LOG_DIR" "$PF_RUN_DIR" \
    "$PF_RECEIPTS_DIR" "$PF_VENVS_DIR" "$PF_RELEASES_DIR" "$PF_CACHE_DIR" \
    "$PF_INBOX_DIR/github" "$HOME/Library/LaunchAgents" "$CLOUDFLARE_HOME"
  if [ "${PF_DRY_RUN:-0}" != "1" ]; then
    chmod 700 "$POWERFARM_HOME" "$PF_STATE_DIR" "$PF_RUN_DIR" "$PF_RECEIPTS_DIR" \
      "$PF_VENVS_DIR" "$PF_RELEASES_DIR" "$PF_CACHE_DIR" "$PF_INBOX_DIR" \
      "$PF_INBOX_DIR/github"
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
  if [ -d "$PF_REPO_ROOT/wheelhouse" ]; then
    if command -v uv >/dev/null 2>&1; then
      run uv pip install --python "$PF_VENV/bin/python" --offline \
        --find-links "$PF_REPO_ROOT/wheelhouse" "powerfarm-kernel==$PF_VERSION"
    else
      run "$PF_VENV/bin/python" -m pip install --no-index \
        --find-links "$PF_REPO_ROOT/wheelhouse" "powerfarm-kernel==$PF_VERSION"
    fi
  elif command -v uv >/dev/null 2>&1; then
    run uv pip install --python "$PF_VENV/bin/python" "$PF_REPO_ROOT"
  else
    run "$PF_VENV/bin/python" -m pip install --upgrade pip
    run "$PF_VENV/bin/python" -m pip install "$PF_REPO_ROOT"
  fi
}

activate_release() {
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would activate release root $PF_REPO_ROOT at $PF_CURRENT_LINK"
    return
  fi
  local pending="$POWERFARM_HOME/.current.$$.tmp"
  ln -s "$PF_REPO_ROOT" "$pending"
  "$PF_PYTHON_BIN" -c 'import os,sys; os.replace(sys.argv[1], sys.argv[2])' \
    "$pending" "$PF_CURRENT_LINK"
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
GITHUB_WEBHOOK_SECRET="\$(security find-generic-password -a powerfarm -s powerfarm.github.webhook-secret -w 2>/dev/null || true)"
export GITHUB_WEBHOOK_SECRET
cd "$PF_CURRENT_LINK"
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
  local domain
  domain="gui/$(id -u)"
  if launchctl print "$domain/$PF_LABEL_WORKER" >/dev/null 2>&1; then
    run launchctl bootout "$domain" "$PF_WORKER_PLIST"
  fi
  run launchctl bootstrap "$domain" "$PF_WORKER_PLIST"
  run launchctl kickstart -k "$domain/$PF_LABEL_WORKER"
}

launchd_unload_worker() {
  local domain
  domain="gui/$(id -u)"
  if launchctl print "$domain/$PF_LABEL_WORKER" >/dev/null 2>&1; then
    run launchctl bootout "$domain" "$PF_WORKER_PLIST"
  fi
}

write_updater_runner() {
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would write $PF_UPDATER_RUNNER"
    return
  fi
  cat > "$PF_UPDATER_RUNNER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "$PF_CURRENT_LINK/deploy/macos/check-update.sh" --env "$PF_ENV_INSTALLED"
EOF
  chmod 700 "$PF_UPDATER_RUNNER"
}

write_updater_plist() {
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would write $PF_UPDATER_PLIST"
    return
  fi
  cat > "$PF_UPDATER_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$PF_LABEL_UPDATER</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PF_UPDATER_RUNNER</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>$POWERFARM_UPDATE_INTERVAL</integer>
  <key>StandardOutPath</key>
  <string>$PF_LOG_DIR/updater.out.log</string>
  <key>StandardErrorPath</key>
  <string>$PF_LOG_DIR/updater.err.log</string>
</dict>
</plist>
EOF
  plutil -lint "$PF_UPDATER_PLIST" >/dev/null
}

launchd_load_updater() {
  local domain
  domain="gui/$(id -u)"
  if launchctl print "$domain/$PF_LABEL_UPDATER" >/dev/null 2>&1; then
    run launchctl bootout "$domain" "$PF_UPDATER_PLIST"
  fi
  run launchctl bootstrap "$domain" "$PF_UPDATER_PLIST"
}

launchd_unload_updater() {
  local domain
  domain="gui/$(id -u)"
  if launchctl print "$domain/$PF_LABEL_UPDATER" >/dev/null 2>&1; then
    run launchctl bootout "$domain" "$PF_UPDATER_PLIST"
  fi
}

write_tunnel_plist() {
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would write $PF_TUNNEL_PLIST"
    return
  fi
  local cloudflared_bin
  cloudflared_bin="$(command -v cloudflared)"
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
  local domain
  domain="gui/$(id -u)"
  if launchctl print "$domain/$PF_LABEL_TUNNEL" >/dev/null 2>&1; then
    run launchctl bootout "$domain" "$PF_TUNNEL_PLIST"
  fi
  run launchctl bootstrap "$domain" "$PF_TUNNEL_PLIST"
  run launchctl kickstart -k "$domain/$PF_LABEL_TUNNEL"
}

launchd_unload_tunnel() {
  local domain
  domain="gui/$(id -u)"
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
  local git_commit
  git_commit="$(git -C "$PF_REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
  local migration
  for migration in "$PF_REPO_ROOT"/supabase/migrations/*.sql; do
    [ -f "$migration" ] || continue
    local filename version name checksum existing ledger_exists
    filename="$(basename "$migration" .sql)"
    version="${filename%%_*}"
    name="${filename#*_}"
    checksum="$(shasum -a 256 "$migration" | awk '{print $1}')"
    if [ "${PF_DRY_RUN:-0}" = "1" ]; then
      log "would verify/apply Supabase migration $filename ($checksum)"
      continue
    fi
    ledger_exists="$(psql "$db_url" -AtX -v ON_ERROR_STOP=1 -c \
      "select (to_regclass('public.powerfarm_schema_migrations') is not null)::text")"
    existing=""
    if [ "$ledger_exists" = "true" ]; then
      existing="$(psql "$db_url" -AtX -v ON_ERROR_STOP=1 -v pf_version="$version" <<'SQL'
select coalesce((select checksum_sha256 from public.powerfarm_schema_migrations where version = :'pf_version'), '');
SQL
)"
    fi
    if [ -n "$existing" ]; then
      [ "$existing" = "$checksum" ] || die "migration checksum changed for $filename"
      log "migration already applied: $filename"
      continue
    fi
    log "applying Supabase migration $filename"
    psql "$db_url" -v ON_ERROR_STOP=1 -f "$migration"
    psql "$db_url" -v ON_ERROR_STOP=1 \
      -v pf_version="$version" -v pf_name="$name" -v pf_checksum="$checksum" \
      -v pf_pack_version="$PF_VERSION" -v pf_git_commit="$git_commit" <<'SQL'
insert into public.powerfarm_schema_migrations(
  version, name, checksum_sha256, pack_version, git_commit
) values (
  :'pf_version', :'pf_name', :'pf_checksum', :'pf_pack_version', nullif(:'pf_git_commit', '')
) on conflict (version) do nothing;
SQL
  done
}

ensure_supabase_storage() {
  require_env_value SUPABASE_PROJECT_REF
  [ -n "$SUPABASE_URL" ] || die "SUPABASE_URL could not be derived"
  local secret_key
  secret_key="$(pf_secret_or_keychain SUPABASE_SECRET_KEY supabase-secret-key || true)"
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would ensure private Supabase buckets $POWERFARM_LEDGER_BUCKET and $POWERFARM_PACKAGES_BUCKET"
    return
  fi
  [ -n "$secret_key" ] || die "SUPABASE_SECRET_KEY is required in env or macOS Keychain"
  SUPABASE_SECRET_KEY="$secret_key" "$PF_PYTHON_BIN" \
    "$PF_SCRIPT_DIR/lib/ensure_supabase_storage.py" "$SUPABASE_URL" \
    "$POWERFARM_LEDGER_BUCKET" "$POWERFARM_PACKAGES_BUCKET"
  unset secret_key
}

mirror_update_package() {
  [ -n "${POWERFARM_PACKAGE_PATH:-}" ] || return 0
  [ -f "$POWERFARM_PACKAGE_PATH" ] || die "package to mirror not found: $POWERFARM_PACKAGE_PATH"
  local secret_key package_hash
  secret_key="$(pf_secret_or_keychain SUPABASE_SECRET_KEY supabase-secret-key || true)"
  package_hash="${POWERFARM_PACKAGE_HASH:-$(shasum -a 256 "$POWERFARM_PACKAGE_PATH" | awk '{print $1}')}"
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    log "would mirror package $package_hash to Supabase Storage"
    return
  fi
  [ -n "$secret_key" ] || die "SUPABASE_SECRET_KEY is required to mirror packages"
  SUPABASE_SECRET_KEY="$secret_key" "$PF_PYTHON_BIN" \
    "$PF_SCRIPT_DIR/lib/mirror_update_package.py" "$SUPABASE_URL" \
    "$POWERFARM_PACKAGES_BUCKET" "$POWERFARM_PACKAGE_PATH" "$package_hash" "$PF_VERSION"
  unset secret_key

  local manifest="$PF_REPO_ROOT/package-manifest.jcs.json"
  [ -f "$manifest" ] || die "package manifest missing: $manifest"
  local manifest_hash git_commit object_size object_path
  manifest_hash="$(shasum -a 256 "$manifest" | awk '{print $1}')"
  git_commit="$("$PF_PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))["git_commit"])' "$manifest")"
  object_size="$(stat -f %z "$POWERFARM_PACKAGE_PATH")"
  object_path="packages/$PF_VERSION/$package_hash.tar.gz"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
    -v pf_hash="$package_hash" -v pf_version="$PF_VERSION" -v pf_commit="$git_commit" \
    -v pf_bucket="$POWERFARM_PACKAGES_BUCKET" -v pf_path="$object_path" \
    -v pf_manifest="$manifest_hash" -v pf_size="$object_size" <<'SQL'
insert into public.update_packages(
  package_hash, version, git_commit, bucket_id, object_path, manifest_hash, object_size
) values (
  :'pf_hash', :'pf_version', :'pf_commit', :'pf_bucket', :'pf_path', :'pf_manifest', :'pf_size'::bigint
) on conflict (package_hash) do nothing;
SQL
  log "mirrored durable update package $package_hash"
}

configure_identity_services() {
  local args=(--env "$PF_ENV_FILE")
  if [ "${PF_DRY_RUN:-0}" = "1" ]; then
    args+=(--dry-run)
  fi
  "$PF_SCRIPT_DIR/configure-auth.sh" "${args[@]}"
  "$PF_SCRIPT_DIR/ensure-oauth-clients.sh" "${args[@]}"
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
  local receipt
  receipt="$PF_RECEIPTS_DIR/$(date -u +%Y%m%dT%H%M%SZ)-$action.json"
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
  if [ -n "${DATABASE_URL:-}" ] && command -v psql >/dev/null 2>&1; then
    local receipt_hash migrations buckets details hostname_value
    receipt_hash="$(shasum -a 256 "$receipt" | awk '{print $1}')"
    migrations="$(psql "$DATABASE_URL" -AtX -v ON_ERROR_STOP=1 -c \
      "select coalesce(jsonb_agg(version order by version), '[]'::jsonb)::text from public.powerfarm_schema_migrations")"
    buckets="[\"$POWERFARM_LEDGER_BUCKET\",\"$POWERFARM_PACKAGES_BUCKET\"]"
    details="$("$PF_PYTHON_BIN" -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1])), separators=(",",":"), sort_keys=True))' "$receipt")"
    hostname_value="$(hostname)"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
      -v pf_hash="$receipt_hash" -v pf_action="$action" -v pf_version="$PF_VERSION" \
      -v pf_commit="$head" -v pf_hostname="$hostname_value" -v pf_api="$POWERFARM_API_HOSTNAME" \
      -v pf_migrations="$migrations" -v pf_buckets="$buckets" -v pf_details="$details" <<'SQL'
insert into public.powerfarm_pack_receipts(
  receipt_hash, action, pack_version, git_commit, hostname, api_hostname,
  migration_versions, storage_buckets, details
) values (
  :'pf_hash', :'pf_action', :'pf_version', nullif(:'pf_commit', ''), :'pf_hostname',
  :'pf_api', :'pf_migrations'::jsonb, :'pf_buckets'::jsonb, :'pf_details'::jsonb
) on conflict (receipt_hash) do nothing;
SQL
  fi
  log "receipt: $receipt"
}
