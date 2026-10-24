#!/usr/bin/env bash
# save-results.sh — fold an evaluation batch into the stocktake results file.
#
# Usage: save-results.sh RESULTS_JSON <<< "$EVAL_JSON"
#   stdin: { "skills": {...}, "mode"?: "full"|"quick", "batch_progress"?: {...} }
#
# Behavior: evaluated_at is always stamped with the current UTC time; incoming
# .skills entries override same-named existing ones while untouched entries are
# kept; .mode / .batch_progress are updated only when present on stdin. The
# write is atomic (temp file + rename) so a crash never truncates the file.

set -euo pipefail

results_json="${1:-}"

if [[ -z "$results_json" ]]; then
  printf 'Error: RESULTS_JSON argument required\n' >&2
  printf 'Usage: save-results.sh RESULTS_JSON <<< "$EVAL_JSON"\n' >&2
  exit 1
fi

batch=$(cat)
if ! jq -e . >/dev/null 2>&1 <<< "$batch"; then
  printf 'Error: stdin is not valid JSON\n' >&2
  exit 1
fi

stamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# First run: the batch itself becomes the results file.
if [[ ! -f "$results_json" ]]; then
  jq --arg at "$stamp" '. + {evaluated_at: $at}' <<< "$batch" > "$results_json"
  exit 0
fi

tmp=$(mktemp "${results_json}.XXXXXX")
trap 'rm -f "$tmp"' EXIT

jq --arg at "$stamp" --argjson batch "$batch" '
  .evaluated_at = $at
  | .skills = ((.skills // {}) + ($batch.skills // {}))
  | if $batch | has("mode")           then .mode = $batch.mode                     else . end
  | if $batch | has("batch_progress") then .batch_progress = $batch.batch_progress else . end
' "$results_json" > "$tmp"

mv "$tmp" "$results_json"
