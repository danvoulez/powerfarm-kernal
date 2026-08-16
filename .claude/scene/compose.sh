#!/usr/bin/env bash
# Projector over the repo: composes the standing declarations with the state
# computed right now, and emits it as SessionStart additionalContext.
#
# This is a projection, not a log: it REPLACES, it never appends. Deleting it
# loses nothing -- every line is either declared in standing.md or recomputed
# from git and the test suite.
#
# Never fails a session: any step may degrade, the script always exits 0.

set -uo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root" || exit 0

say() { printf '%s\n' "$*" >>"$out"; }
out="$(mktemp -t pf-scene)"
trap 'rm -f "$out"' EXIT

# ---- cut: where history stands right now ------------------------------------
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
commit="$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
subject="$(git log -1 --pretty=%s 2>/dev/null || echo '?')"
dirty="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"

say "══════ POWERFARM — CENA COMPOSTA ══════"
say "cut: ${branch} @ ${commit} — ${subject}"
say "data: $(date '+%Y-%m-%d %H:%M')"
say ""

# ---- the declared part -------------------------------------------------------
if [ -f .claude/scene/standing.md ]; then
  cat .claude/scene/standing.md >>"$out"
  say ""
fi

# ---- the computed part -------------------------------------------------------
say "# ESTADO VERIFICADO AGORA (recomputado, não lembrado)"

if [ -x .venv/bin/python ]; then
  result="$(.venv/bin/python -m pytest -q 2>&1 | tail -1)"
  say "pytest      : ${result:-sem saída}"
else
  say "pytest      : .venv ausente — não executado"
fi

say "migrations  : $(find supabase/migrations -maxdepth 1 -name '*.sql' 2>/dev/null | wc -l | tr -d ' ') arquivos (selados; só acrescentar)"
say "worker      : /commit responde 501 até o PostgresStore existir"
say ""

if [ "$dirty" != "0" ]; then
  say "# NÃO COMMITADO — ${dirty} arquivo(s)"
  git status --porcelain 2>/dev/null | sed 's/^/  /' >>"$out"
  say ""
  say "Trabalho em curso, não sujeira. Ler o diff antes de propor mudança nestes."
else
  say "# ÁRVORE LIMPA"
fi

say ""
say "══════ fim da cena — nada aqui precisa ser buscado ══════"

jq -Rs '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: .}}' <"$out" 2>/dev/null \
  || printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"cena indisponível"}}\n'
exit 0
