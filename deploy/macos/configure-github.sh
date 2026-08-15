#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOSITORY="${POWERFARM_GITHUB_REPOSITORY:-danvoulez/powerfarm-kernal}"
DRY_RUN=0
[ "${1:-}" != "--dry-run" ] || DRY_RUN=1
command -v gh >/dev/null 2>&1 || { printf '%s\n' 'gh CLI not found' >&2; exit 1; }

ruleset="$REPO_ROOT/.github/rulesets/main.json"
if [ "$DRY_RUN" = "1" ]; then
  jq empty "$ruleset"
  printf 'would converge GitHub ruleset powerfarm-main on %s\n' "$REPOSITORY"
  printf 'would enable secret scanning and push protection\n'
  exit 0
fi

ruleset_id="$(gh api "repos/$REPOSITORY/rulesets" --jq '.[] | select(.name == "powerfarm-main") | .id' | head -1)"
if [ -n "$ruleset_id" ]; then
  gh api --method PUT "repos/$REPOSITORY/rulesets/$ruleset_id" --input "$ruleset" >/dev/null
  printf 'updated GitHub ruleset powerfarm-main\n'
else
  gh api --method POST "repos/$REPOSITORY/rulesets" --input "$ruleset" >/dev/null
  printf 'created GitHub ruleset powerfarm-main\n'
fi

gh api --method PATCH "repos/$REPOSITORY" --input - >/dev/null <<'JSON'
{
  "security_and_analysis": {
    "secret_scanning": {"status": "enabled"},
    "secret_scanning_push_protection": {"status": "enabled"},
    "secret_scanning_validity_checks": {"status": "enabled"}
  }
}
JSON
printf 'enabled GitHub secret scanning protections\n'
