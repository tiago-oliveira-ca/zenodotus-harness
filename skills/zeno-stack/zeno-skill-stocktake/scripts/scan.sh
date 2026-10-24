#!/usr/bin/env bash
# scan.sh — inventory skill markdown files for the stocktake audit.
#
# Usage: scan.sh [--target claude|codex] [PROJECT_SKILLS_DIR]
#   Claude is the default. Project skills default to $PWD/.<target>/skills.
#
# Output (stdout): one JSON document —
#   { scan_summary: { target, global: {found,count}, project: {found,path,count} },
#     skills: [ {path,name,description,mtime,sha256} ] }
#   scan_summary counts report `files` (all *.md) and `skills` (SKILL.md only) separately.
#
# Environment (test seams; leave unset in normal use):
#   SKILL_STOCKTAKE_TARGET       claude (default) or codex
#   SKILL_STOCKTAKE_GLOBAL_DIR   overrides the target's global skills directory
#   SKILL_STOCKTAKE_PROJECT_DIR   overrides the project dir argument

set -euo pipefail

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
global_dir="${SKILL_STOCKTAKE_GLOBAL_DIR:-$default_global}"
project_dir="${SKILL_STOCKTAKE_PROJECT_DIR:-${project_arg:-$default_project}}"

# A project dir that exists but isn't a .claude/skills path is probably a
# mis-typed argument — warn, don't refuse (the caller may know better).
if [[ -d "$project_dir" && "$project_dir" != */.$target/skills* ]]; then
  printf 'Warning: project dir does not look like a .%s/skills path: %s\n' "$target" "$project_dir" >&2
fi

# Emit one record per markdown file: abs-path <US> display-path <US> mtime <US> name <US> description
# US (\x1f) is the field separator — descriptions may legally contain tabs.
# Frontmatter parsing is single-line values plus folded blocks (`key: >` with
# indented continuation lines); nested YAML is out of scope here.
inventory() {
  local dir="$1" file display mtime meta
  while IFS= read -r file; do
    display="$file"
    [[ "$file" == "$HOME"/* ]] && display="~${file#"$HOME"}"
    mtime=$(date -u -r "$file" +%Y-%m-%dT%H:%M:%SZ)
    # Content hash, because mtime cannot detect change here: install.sh copies with `cp -R`
    # (no -p), so every install rewrites every timestamp identically and Quick Scan would
    # report "everything changed" forever. Hash is what quick-diff.sh must compare.
    hash=$(shasum -a 256 "$file" 2>/dev/null | cut -d' ' -f1)
    meta=$(awk '
      NR==1 && $0 !~ /^---[[:space:]]*$/ { exit }          # no frontmatter at all
      /^---[[:space:]]*$/ { if (++fence == 2) exit; next }
      fence != 1 { next }
      /^name:[[:space:]]*/ {
        cur = "n"; n = $0; sub(/^name:[[:space:]]*/, "", n); gsub(/^"|"$/, "", n); next
      }
      /^description:[[:space:]]*/ {
        cur = "d"; d = $0; sub(/^description:[[:space:]]*/, "", d)
        gsub(/^"|"$/, "", d); sub(/^[>|][+-]?[[:space:]]*$/, "", d); next
      }
      /^[[:space:]]+[^[:space:]]/ && cur == "d" {           # folded-block continuation
        line = $0; gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
        d = (d == "" ? line : d " " line); next
      }
      /^[A-Za-z_-]+:/ { cur = "" }                          # any other top-level key
      END { printf "%s\x1f%s", n, d }
    ' "$file")
    printf '%s\x1f%s\x1f%s\x1f%s\x1f%s\n' "$file" "$display" "$mtime" "$hash" "$meta"
  done < <(find "$dir" -type f -name '*.md' 2>/dev/null | LC_ALL=C sort)
}

global_rows=""; global_found=false
if [[ -d "$global_dir" ]]; then
  global_found=true
  global_rows=$(inventory "$global_dir")
fi

project_rows=""; project_found=false; project_path=""
if [[ -d "$project_dir" ]]; then
  project_found=true
  project_path="$project_dir"
  project_rows=$(inventory "$project_dir")
fi

global_count=$(grep -c . <<< "$global_rows" || true)
project_count=$(grep -c . <<< "$project_rows" || true)
# Files vs skills: the glob picks up every *.md (references/, templates), but only SKILL.md
# files are skills. Reporting one number for both inflated the inventory an audit reasons over.
global_skills=$(grep -c '/SKILL\.md' <<< "$global_rows" || true)
project_skills=$(grep -c '/SKILL\.md' <<< "$project_rows" || true)

{ printf '%s\n' "$global_rows"; printf '%s\n' "$project_rows"; } | jq -Rn \
  --argjson gfound "$global_found" --argjson gcount "$global_count" \
  --argjson gskills "$global_skills" --argjson pskills "$project_skills" \
  --argjson pfound "$project_found" --argjson pcount "$project_count" \
  --arg ppath "$project_path" --arg target "$target" \
  '
  [ inputs | select(length > 0) | split("")
    | { path: .[1], name: .[4], description: .[5],
        mtime: .[2], sha256: .[3] } ]
  | { scan_summary: {
        target: $target,
        global:  { found: $gfound, files: $gcount, skills: $gskills },
        project: { found: $pfound, path: $ppath, files: $pcount, skills: $pskills } },
      skills: . }
  '
