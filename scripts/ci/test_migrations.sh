#!/usr/bin/env bash
set -euo pipefail

PGBIN="${PGBIN:-}"
if [ -z "$PGBIN" ]; then
  for candidate in /usr/lib/postgresql/17/bin /opt/homebrew/opt/postgresql@17/bin /opt/homebrew/opt/postgresql@15/bin; do
    if [ -x "$candidate/postgres" ]; then
      PGBIN="$candidate"
      break
    fi
  done
fi
[ -n "$PGBIN" ] || { printf '%s\n' 'PostgreSQL 15+ binaries not found' >&2; exit 1; }

TMP_PG="$(mktemp -d "${TMPDIR:-/tmp}/powerfarm-ci-pg.XXXXXX")"
PORT="${POWERFARM_TEST_PG_PORT:-55449}"
cleanup() {
  "$PGBIN/pg_ctl" -D "$TMP_PG/data" -m immediate stop >/dev/null 2>&1 || true
  rm -rf "$TMP_PG"
}
trap cleanup EXIT
"$PGBIN/initdb" -D "$TMP_PG/data" -A trust -U postgres >/dev/null
"$PGBIN/pg_ctl" -D "$TMP_PG/data" -o "-p $PORT -k $TMP_PG" -l "$TMP_PG/postgres.log" start >/dev/null
PSQL=("$PGBIN/psql" -h "$TMP_PG" -p "$PORT" -U postgres -d postgres -v ON_ERROR_STOP=1 -X)
"${PSQL[@]}" <<'SQL' >/dev/null
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
create role supabase_admin nologin superuser;
create schema auth;
create table auth.users (id uuid primary key);
SQL

export DATABASE_URL="host=$TMP_PG port=$PORT user=postgres dbname=postgres"
# Ordered migrations are applied once.  Idempotency belongs to the checksum
# ledger: a later schema migration may intentionally make an earlier migration
# inapplicable to the evolved schema, so replaying every historical file is not
# a valid production operation.
apply_supabase_migrations() {
  local migration filename version name checksum ledger_exists existing
  for migration in supabase/migrations/*.sql; do
    filename="$(basename "$migration" .sql)"
    version="${filename%%_*}"
    name="${filename#*_}"
    checksum="$(shasum -a 256 "$migration" | awk '{print $1}')"
    ledger_exists="$("${PSQL[@]}" -Atc \
      "select (to_regclass('public.powerfarm_schema_migrations') is not null)::text")"
    existing=""
    if [ "$ledger_exists" = "true" ]; then
      existing="$("${PSQL[@]}" -At -v pf_version="$version" <<'SQL'
select coalesce((select checksum_sha256 from public.powerfarm_schema_migrations where version = :'pf_version'), '');
SQL
)"
    fi
    if [ -n "$existing" ]; then
      [ "$existing" = "$checksum" ] || {
        printf 'migration checksum changed for %s\n' "$filename" >&2
        return 1
      }
      continue
    fi
    "${PSQL[@]}" -f "$migration"
    "${PSQL[@]}" -v pf_version="$version" -v pf_name="$name" \
      -v pf_checksum="$checksum" <<'SQL'
insert into public.powerfarm_schema_migrations(
  version, name, checksum_sha256, pack_version, git_commit
) values (
  :'pf_version', :'pf_name', :'pf_checksum', 'ci', null
) on conflict (version) do nothing;
SQL
  done
}
apply_supabase_migrations
apply_supabase_migrations
ledger_count="$("${PSQL[@]}" -Atc 'select count(*) from public.powerfarm_schema_migrations')"
expected_count="$(find supabase/migrations -maxdepth 1 -name '*.sql' | wc -l | tr -d ' ')"
[ "$ledger_count" = "$expected_count" ] || {
  printf 'installer migration ledger has %s entries, expected %s\n' \
    "$ledger_count" "$expected_count" >&2
  exit 1
}
printf 'installer migration ledger passed\n'

"${PSQL[@]}" <<'SQL' >/dev/null
create role powerfarm_worker_test login;
grant powerfarm_worker to powerfarm_worker_test;
SQL
if "$PGBIN/psql" -h "$TMP_PG" -p "$PORT" -U service_role -d postgres \
  -Atc 'select count(*) from public.objects' >/dev/null 2>&1; then
  printf '%s\n' 'service_role retained direct ledger access' >&2
  exit 1
fi
"$PGBIN/psql" -h "$TMP_PG" -p "$PORT" -U powerfarm_worker_test -d postgres \
  -Atc 'select count(*) from public.objects' >/dev/null
if "$PGBIN/psql" -h "$TMP_PG" -p "$PORT" -U powerfarm_worker_test -d postgres \
  -Atc "insert into public.objects(hash,canon,kind) values(repeat('a',64),'x','test')" \
  >/dev/null 2>&1; then
  printf '%s\n' 'worker gained direct ledger insert' >&2
  exit 1
fi
if "${PSQL[@]}" -Atc \
  "select has_function_privilege('powerfarm_worker_test', 'powerfarm_internal.commit_act_internal(text,bytea,text,text,text,jsonb,jsonb,text,jsonb,jsonb,jsonb,text,text,text,text,text)', 'execute')" \
  | grep -qx t; then
  printf '%s\n' 'worker can still call bare commit_act_internal' >&2
  exit 1
fi
if "$PGBIN/psql" -h "$TMP_PG" -p "$PORT" -U powerfarm_worker_test -d postgres \
  -Atc "insert into public.principal_bindings(issuer,subject,identity_hash,linked_act) values('x','y',repeat('a',64),repeat('b',64))" \
  >/dev/null 2>&1; then
  printf '%s\n' 'worker retained a direct principal-binding writer' >&2
  exit 1
fi
printf 'migration security invariants passed\n'

# PF-21 at the real admission boundary. conformance/test_pf21.py proves the
# Kernel resolves semantic dependencies to exact definitions; this proves the
# function that actually admits Acts does the same. Redundant on purpose -- if
# the two layers ever disagree, the disagreement is the finding.
"${PSQL[@]}" -f conformance/sql/pf21_admission.sql >/dev/null
printf 'PF-21 admission conformance passed\n'

"${PSQL[@]}" -f conformance/sql/m1_admission.sql >/dev/null
printf 'M1 transactional admission conformance passed\n'

# PF-07, PF-10, PF-12 and "one consequence per Command" are enforced by triggers,
# constraints and a partial unique index. Each case below attempts the forbidden
# thing: a dropped trigger and a working one look identical to anything that only
# reads the migration text.
"${PSQL[@]}" -f conformance/sql/ledger_invariants.sql >/dev/null
printf 'ledger invariant conformance passed\n'
