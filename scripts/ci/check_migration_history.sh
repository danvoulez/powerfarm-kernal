#!/usr/bin/env bash
set -euo pipefail

base_ref="${1:-origin/main}"
marker="supabase/migrations/.sealed"
if ! git cat-file -e "$base_ref:$marker" 2>/dev/null; then
  printf 'migration history is being sealed by this change; no prior seal found\n'
  exit 0
fi

status=0
while IFS=$'\t' read -r change path rest; do
  case "$change" in
    M|D|R*|C*)
      if [[ "$path" == supabase/migrations/*.sql ]] || [[ "$rest" == supabase/migrations/*.sql ]]; then
        printf 'published migration is immutable: %s %s %s\n' "$change" "$path" "$rest" >&2
        status=1
      fi
      ;;
  esac
done < <(git diff --name-status "$base_ref"...HEAD -- supabase/migrations)
exit "$status"
