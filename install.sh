#!/usr/bin/env bash
# Zenodotus installer — mirrors the single-source library into ~/.claude and
# self-wires the always-on SessionStart hook and the Stop cost-tracker hook.
# Copy-only (no --delete), idempotent.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_HOME:-$HOME/.claude}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

echo "Zenodotus → installing into: $DEST"
mkdir -p "$DEST/skills" "$DEST/agents" "$DEST/commands" "$DEST/hooks"

# --- Skills / agents / commands / hooks (preserves nested sub-skills) ---
# hooks: copy only the Claude-target *.sh scripts — hooks/codex/ belongs to install-codex.sh's
# target and must not pollute ~/.claude/hooks (it also broke the "2 hooks" inventory count).
cp -R "$SRC/skills/."   "$DEST/skills/"
cp -R "$SRC/agents/."   "$DEST/agents/"
cp -R "$SRC/commands/." "$DEST/commands/"
cp "$SRC"/hooks/*.sh    "$DEST/hooks/"
chmod +x "$DEST"/hooks/*.sh 2>/dev/null || true
echo "  ✓ skills / agents / commands / hooks mirrored"

# --- CLAUDE.md: back up before overwriting (never clobber silently) ---
if [ -f "$DEST/CLAUDE.md" ] && ! cmp -s "$SRC/CLAUDE.md" "$DEST/CLAUDE.md"; then
  cp "$DEST/CLAUDE.md" "$DEST/CLAUDE.md.bak-$STAMP"   # keep the old version
  cp "$SRC/CLAUDE.md" "$DEST/CLAUDE.md"               # then install the new one
  echo "  ✓ CLAUDE.md updated (previous saved to CLAUDE.md.bak-$STAMP)"
else
  cp "$SRC/CLAUDE.md" "$DEST/CLAUDE.md"
  echo "  ✓ CLAUDE.md installed"
fi

# --- Self-wire the SessionStart and Stop hooks into settings.json (idempotent) ---
# NOTE: this must be settings.json, not settings.local.json. Claude Code only recognizes
# settings.local.json as a PROJECT-scoped file (<repo-root>/.claude/settings.local.json,
# read when $HOME is a git repo root and the CLI is launched from within it). A file at
# the literal global path $HOME/.claude/settings.local.json is never loaded — writing hooks
# there silently no-ops forever. See https://code.claude.com/docs/en/settings.md.
SETTINGS="$DEST/settings.json"
python3 - "$SETTINGS" "$STAMP" \
  "SessionStart" "$SRC/session-hook.fragment.json" "zeno-session-start.sh" \
  "Stop" "$SRC/cost-hook.fragment.json" "zeno-cost-tracker.sh" \
<<'PY'
import json, os, sys, shutil

settings_path, stamp = sys.argv[1], sys.argv[2]
settings_name = os.path.basename(settings_path)
specs = list(zip(sys.argv[3::3], sys.argv[4::3], sys.argv[5::3]))  # (event, fragment_path, marker)

data = {}
if os.path.exists(settings_path):
    try:
        data = json.load(open(settings_path))
    except Exception:
        print(f"  · {settings_name} unreadable — leaving it alone; register hooks by hand.")
        sys.exit(0)

hooks = data.setdefault("hooks", {})
changed = False

def has_marker(entries, marker):
    return any(marker in h.get("command", "")
               for e in entries for h in e.get("hooks", []))

for event, fragment_path, marker in specs:
    # A missing/corrupt fragment must not abort the install mid-way with a raw
    # traceback (files are already copied by this point) — skip it with a message.
    try:
        frag = json.load(open(fragment_path))[event]
    except (OSError, ValueError, KeyError) as exc:
        print(f"  ! {event} hook NOT registered — fragment unusable ({fragment_path}: {exc}); register by hand.")
        continue
    entries = hooks.setdefault(event, [])
    if has_marker(entries, marker):
        print(f"  ✓ {event} hook already registered")
        continue
    entries.extend(frag)
    changed = True
    print(f"  ✓ {event} hook registered in {settings_name}")

if changed:
    if os.path.exists(settings_path):
        shutil.copy(settings_path, settings_path + f".bak-{stamp}")
    json.dump(data, open(settings_path, "w"), indent=2)
PY

# --- Assert the installed surface against source by NAME SET, not count (invariant #6) ---
# Copy-only never deletes, so a file pruned or renamed in source lingers in $DEST silently —
# and a rename nets out to zero count drift. Compare sorted name listings for all four dirs.
# (Skills compare visible top-level dirs, same as CLAUDE.md's inventory, so stray hidden dirs
# like .idea don't trip a false drift; hooks compare *.sh only — codex/ is not installed here.)
list_names() {  # $1=dir  $2=mode(dirs|files|sh)
  case "$2" in
    dirs)  find "$1" -maxdepth 1 -mindepth 1 -type d ! -name '.*' -exec basename {} \; ;;
    files) find "$1" -maxdepth 1 -mindepth 1 -type f -name '*.md' -exec basename {} \; ;;
    sh)    find "$1" -maxdepth 1 -mindepth 1 -type f -name '*.sh' -exec basename {} \; ;;
  esac | LC_ALL=C sort
}
drift=0
for spec in "skills dirs" "agents files" "commands files" "hooks sh"; do
  d="${spec%% *}"; mode="${spec##* }"
  extra=$(comm -13 <(list_names "$SRC/$d" "$mode") <(list_names "$DEST/$d" "$mode"))
  missing=$(comm -23 <(list_names "$SRC/$d" "$mode") <(list_names "$DEST/$d" "$mode"))
  if [ -n "$extra" ]; then
    drift=1
    echo "  ! DRIFT in $DEST/$d — not in source (copy-only never deletes; remove by hand):"
    echo "$extra" | sed 's/^/      /'
  fi
  if [ -n "$missing" ]; then
    drift=1
    echo "  ! DRIFT in $DEST/$d — present in source but missing from install:"
    echo "$missing" | sed 's/^/      /'
  fi
done
[ "$drift" = 0 ] && echo "  ✓ name-set drift check clean (skills/agents/commands/hooks)"
sk=$(list_names "$DEST/skills" dirs | wc -l | tr -d ' ')
# Exclude _agent-template.md and REGISTRY.md — reference files, not agents, so this count
# matches the "24 agents" the docs state rather than the 26 files actually in the directory.
ag=$(ls "$DEST/agents" | grep -v -e '^_agent-template\.md$' -e '^REGISTRY\.md$' | wc -l | tr -d ' ')
cm=$(ls "$DEST/commands" | wc -l | tr -d ' ')
echo "  · installed surface: skills=$sk agents=$ag commands=$cm hooks=$(list_names "$DEST/hooks" sh | wc -l | tr -d ' ')"

echo
echo "Done. Zenodotus is the single library — no plugins to enable for it."
