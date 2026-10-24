#!/usr/bin/env bash
# Zenodotus installer — Codex CLI target. Mirrors the single-source library into ~/.codex via
# tools/codex/build_codex.py (transform + fold), and self-wires the SessionStart/Stop hooks into
# ~/.codex/hooks.json. Sibling to install.sh (Claude Code); that script is untouched by this one.
#
# Ownership-bounded synchronization from the generator's output: generated top-level skill
# directories are replaced exactly and tracked in a manifest, while Codex-owned `.system` and
# unrelated user skills are preserved. Zero external Python dependencies (stdlib tomllib,
# Python 3.11+ — the same constraint build_codex.py already carries).

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=tools/install-common.sh
. "$SRC/tools/install-common.sh"
detect_os
find_python 11
DEST="${CODEX_HOME:-$HOME/.codex}"
# The hook command registered in hooks.json embeds this path inside double quotes and is run later by
# Codex through a shell, so characters that could break out of the quotes are refused up front.
# (On Git Bash the check runs on the forward-slash form that is actually written, so Windows paths pass.)
case "$(to_native_path "$DEST")" in
  *[\"\$\`\\]*|*$'\n'*|*$'\r'*)
    echo "error: CODEX_HOME contains a character that is unsafe in a hook command (\" \$ \` \\ or a newline): $DEST" >&2
    exit 1 ;;
esac
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DRY_RUN=0
OUT_DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --out) OUT_DIR="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [ "$DRY_RUN" = "1" ]; then
  if [ -z "$OUT_DIR" ]; then
    echo "--dry-run requires --out <scratch-dir>" >&2
    exit 1
  fi
  echo "Zenodotus (Codex, dry-run) → generating into: $OUT_DIR"
  "$PY" "$SRC/tools/codex/build_codex.py" --out "$OUT_DIR"
  echo "Dry run only — $DEST was not touched."
  exit 0
fi

echo "Zenodotus → installing into: $DEST"
mkdir -p "$DEST"

# --- Generate the transformed+folded skills tree, then sync only the managed surface ---
GEN_BASE="$(mktemp -d)"
GEN_OUT="$GEN_BASE/generated"
trap 'rm -rf "$GEN_BASE"' EXIT
"$PY" "$SRC/tools/codex/build_codex.py" --out "$GEN_OUT"
mkdir -p "$DEST/skills"
MANAGED_SKILLS="$DEST/.zenodotus-managed-skills"
"$PY" - "$GEN_OUT/skills" "$DEST/skills" "$MANAGED_SKILLS" <<'PY'
import os
from pathlib import Path
import shutil
import sys
import tempfile

source_root = Path(sys.argv[1])
destination_root = Path(sys.argv[2])
manifest_path = Path(sys.argv[3])

current = {path.name for path in source_root.iterdir() if path.is_dir()}
previous = set()
if manifest_path.exists():
    previous = {line.strip() for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()}

managed = previous | current
for name in managed:
    if name in {".", "..", ".system"} or "/" in name or os.sep in name:
        raise SystemExit(f"unsafe managed skill name in manifest: {name!r}")

for name in sorted(managed):
    source = source_root / name
    destination = destination_root / name
    if destination.is_symlink() or destination.is_file():
        destination.unlink()
    elif destination.is_dir():
        shutil.rmtree(destination)
    if source.is_dir():
        shutil.copytree(source, destination)

manifest_path.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile(
    "w", dir=manifest_path.parent, prefix=f"{manifest_path.name}.", delete=False,
    encoding="utf-8", newline="\n",
) as manifest_file:
    manifest_file.write("".join(f"{name}\n" for name in sorted(current)))
    temporary_manifest = Path(manifest_file.name)
temporary_manifest.replace(manifest_path)
PY
echo "  ✓ skills synchronized (generated + folded; foreign skills preserved)"

# --- AGENTS.md: back up before overwriting (never clobber silently) ---
if [ -f "$DEST/AGENTS.md" ] && ! cmp -s "$SRC/AGENTS.md" "$DEST/AGENTS.md"; then
  cp "$DEST/AGENTS.md" "$DEST/AGENTS.md.bak-$STAMP"
  cp "$SRC/AGENTS.md" "$DEST/AGENTS.md"
  echo "  ✓ AGENTS.md updated (previous saved to AGENTS.md.bak-$STAMP)"
else
  cp "$SRC/AGENTS.md" "$DEST/AGENTS.md"
  echo "  ✓ AGENTS.md installed"
fi

# --- Self-wire the SessionStart and Stop hooks into hooks.json (idempotent) ---
# Confirmed against a live Codex CLI install (0.147.0), not guessed: Codex reads hook
# registrations from $CODEX_HOME/hooks.json — a Claude-Code-settings.json-shaped JSON file
# ({"hooks": {"<Event>": [{"hooks": [{"type": "command", "command": ...}]}]}}) — not from a
# `[[hooks]]` array-of-tables in config.toml as this script originally assumed. config.toml only
# holds a separate `[hooks.state]` trust-hash cache Codex populates once a hooks.json entry has
# been approved; this installer doesn't (and can't safely) forge that trust, so a freshly
# registered hook still needs a one-time interactive approval in Codex before it will fire — see
# STORY-codex-hooks-port's Decisions log. Mirrors install.sh's idempotent JSON-merge pattern
# (marker string in the command, never rewrite existing entries). Registers each event
# independently, only when its own script actually exists under hooks/codex/ — STORY-codex-hooks-port
# lands its two hooks incrementally (SessionStart's I/O contract is confirmed live; Stop's is still
# blocked on Codex usage quota), so an all-or-nothing gate would either wire a hook whose script
# doesn't exist yet or withhold a hook that's already verified and ready.
HOOKS_JSON="$DEST/hooks.json"
HOOKS_SRC_DIR="$SRC/hooks/codex"
if [ -d "$HOOKS_SRC_DIR" ] && ls "$HOOKS_SRC_DIR"/*.sh >/dev/null 2>&1; then
  mkdir -p "$DEST/hooks"
  cp -R "$HOOKS_SRC_DIR/." "$DEST/hooks/"
  for managed_hook in zeno-session-start.sh zeno-cost-tracker.sh; do
    if [ ! -f "$HOOKS_SRC_DIR/$managed_hook" ]; then
      rm -f "$DEST/hooks/$managed_hook"
    fi
  done
  chmod +x "$DEST"/hooks/*.sh 2>/dev/null || true
  HOOKS_DEST_NATIVE="$(to_native_path "$DEST")"
  "$PY" - "$HOOKS_JSON" "$STAMP" "$HOOKS_DEST_NATIVE" "$HOOKS_SRC_DIR" \
    "SessionStart" "zeno-session-start.sh" \
    "Stop" "zeno-cost-tracker.sh" \
<<'PY'
import json, os, sys, shutil

hooks_path, stamp, dest, source_dir = sys.argv[1:5]
hooks_name = os.path.basename(hooks_path)
specs = list(zip(sys.argv[5::2], sys.argv[6::2]))  # (event, script)

data = {}
if os.path.exists(hooks_path):
    try:
        data = json.load(open(hooks_path, encoding="utf-8"))
    except Exception:
        print(f"  · {hooks_name} unreadable — leaving it alone; register hooks by hand.")
        sys.exit(0)

hooks = data.setdefault("hooks", {})
changed = False

def has_marker(entries, marker):
    return any(marker in h.get("command", "")
               for e in entries for h in e.get("hooks", []))

def without_marker(entries, marker):
    kept_entries = []
    for entry in entries:
        kept_hooks = [
            hook for hook in entry.get("hooks", [])
            if marker not in hook.get("command", "")
        ]
        if kept_hooks:
            kept_entry = dict(entry)
            kept_entry["hooks"] = kept_hooks
            kept_entries.append(kept_entry)
    return kept_entries

for event, script in specs:
    marker = f"hooks/{script}"
    entries = hooks.setdefault(event, [])
    if not os.path.isfile(os.path.join(source_dir, script)):
        kept_entries = without_marker(entries, marker)
        if kept_entries != entries:
            hooks[event] = kept_entries
            changed = True
            print(f"  ✓ obsolete {event} hook registration removed")
        else:
            print(f"  · {script} not present yet — {event} hook remains unregistered")
        continue
    if has_marker(entries, marker):
        print(f"  ✓ {event} hook already registered")
        continue
    entries.append({"hooks": [{"type": "command", "command": f"bash \"{dest}/hooks/{script}\""}]})
    changed = True
    print(f"  ✓ {event} hook registered in {hooks_name} (needs one-time approval in Codex)")

if changed:
    if os.path.exists(hooks_path):
        shutil.copy(hooks_path, hooks_path + f".bak-{stamp}")
    # Atomic write: a crash mid-write must never leave a truncated hooks file.
    import tempfile
    directory = os.path.dirname(os.path.abspath(hooks_path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".zeno-tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
            json.dump(data, out, indent=2)
        if os.path.exists(hooks_path):
            shutil.copymode(hooks_path, tmp)
        os.replace(tmp, hooks_path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
PY
else
  echo "  · hooks/codex/*.sh not present yet — skipping hook registration (see STORY-codex-hooks-port; not guessed)"
fi

# --- Assert managed surface counts; foreign directories are deliberately excluded ---
count_dirs() { find "$1" -maxdepth 1 -mindepth 1 -type d ! -name '.*' | wc -l | tr -d ' '; }
sk=$(wc -l < "$MANAGED_SKILLS" | tr -d ' ')
src_sk=$(count_dirs "$GEN_OUT/skills")
echo "  · managed surface: skills=$sk (generated tree has $src_sk top-level dirs)"
if [ "$sk" != "$src_sk" ]; then
  echo "  ! DRIFT: manifest has $sk top-level dirs but the freshly generated tree has $src_sk"
fi

echo
echo "Done. Zenodotus (Codex target) installed from the same single source as install.sh."
