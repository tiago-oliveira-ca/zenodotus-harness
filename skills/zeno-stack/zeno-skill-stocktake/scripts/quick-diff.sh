#!/usr/bin/env bash
# quick-diff.sh — list skill files changed or added since the last stocktake.
#
# Usage: quick-diff.sh RESULTS_JSON [--target claude|codex] [PROJECT_SKILLS_DIR]
#   Claude is the default. Project skills default to $PWD/.<target>/skills.
#
# Output (stdout): JSON array of {path, sha256, is_new} — [] when nothing changed.
# A file is emitted when it is unknown to RESULTS_JSON (is_new: true) or its
# content hash differs from the one recorded in results.json (is_new: false).
#
# Environment (test seams; leave unset in normal use):
#   SKILL_STOCKTAKE_TARGET       claude (default) or codex
#   SKILL_STOCKTAKE_GLOBAL_DIR   overrides the target's global skills directory
#   SKILL_STOCKTAKE_PROJECT_DIR   overrides the project dir argument

set -euo pipefail

results_json="${1:-}"
shift || true
target="${SKILL_STOCKTAKE_TARGET:-claude}"
project_arg=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || { printf 'Error: --target requires claude or codex\n' >&2; exit 2; }
      target="$2"; shift 2 ;;
    --target=*) target="${1#*=}"; shift ;;
    *) project_arg="$1"; shift ;;
  esac
done
case "$target" in
  claude) default_global="$HOME/.claude/skills"; default_project="$PWD/.claude/skills" ;;
  codex) default_global="${CODEX_HOME:-$HOME/.codex}/skills"; default_project="$PWD/.codex/skills" ;;
  *) printf 'Error: target must be claude or codex: %s\n' "$target" >&2; exit 2 ;;
esac
project_dir="${SKILL_STOCKTAKE_PROJECT_DIR:-${project_arg:-$default_project}}"
global_dir="${SKILL_STOCKTAKE_GLOBAL_DIR:-$default_global}"

if [[ -z "$results_json" || ! -f "$results_json" ]]; then
  printf 'Error: RESULTS_JSON not found: %s\n' "${results_json:-<empty>}" >&2
  exit 1
fi

if [[ -d "$project_dir" && "$project_dir" != */.$target/skills* ]]; then
  printf 'Warning: project dir does not look like a .%s/skills path: %s\n' "$target" "$project_dir" >&2
fi

evaluated_at=$(jq -r '.evaluated_at // empty' "$results_json")

# ISO 8601 UTC or nothing — a malformed cutoff would turn every string
# comparison below into quiet nonsense, so refuse it up front.
if [[ ! "$evaluated_at" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]]; then
  printf 'Error: invalid or missing evaluated_at in %s: %s\n' "$results_json" "${evaluated_at:-<missing>}" >&2
  exit 1
fi

# Emit "display-path <US> sha256 <US> owning-skill" per markdown file across both roots.
# The owning skill is the nearest ancestor directory containing a SKILL.md — so a change to a
# references/ or frameworks/ file correctly re-triggers the skill that ships it. The previous
# version compared every *.md against a cache keyed only on SKILL.md paths, so all 60 non-SKILL.md
# files reported is_new on every run and the "no changes" branch could never fire (fixed 2026-08-18).
list_files() {
  local dir file display owner
  for dir in "$global_dir" "$project_dir"; do
    [[ -d "$dir" ]] || continue
    while IFS= read -r file; do
      display="$file"
      [[ "$file" == "$HOME"/* ]] && display="~${file#"$HOME"}"
      owner="$(dirname "$file")"
      while [[ "$owner" != "/" && "$owner" != "$dir" && ! -f "$owner/SKILL.md" ]]; do
        owner="$(dirname "$owner")"
      done
      [[ -f "$owner/SKILL.md" ]] || owner=""
      [[ -n "$owner" && "$owner" == "$HOME"/* ]] && owner="~${owner#"$HOME"}"
      printf '%s\x1f%s\x1f%s\n' "$display" "$(shasum -a 256 "$file" | cut -d' ' -f1)" "$owner"
    done < <(find "$dir" -type f -name '*.md' 2>/dev/null | LC_ALL=C sort)
  done
}

# Known hashes come from results.json's `files` map (every scanned *.md). A cache written before
# that map existed falls back to the per-skill sha256, which covers SKILL.md files only — in that
# case the first run after upgrading re-evaluates everything once, by design.
list_files | jq -Rn --slurpfile results "$results_json" '
  ( ($results[0].files // {}) ) as $byfile
  | ( [ $results[0].skills[]? | select(.sha256) | {key: .path, value: .sha256} ] | from_entries ) as $byskill
  | ( $byskill + $byfile ) as $known
  | [ inputs
      | select(length > 0)
      | split("\u001f")
      | { path: .[0], sha256: .[1], skill: .[2] }
      | . + { cached: ($known[.path] // null) }
      | . + { is_new: (.cached == null) }
      | select(.is_new or .cached != .sha256)
      | { path, sha256, is_new, skill } ]
'
