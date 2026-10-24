#!/usr/bin/env bash
# End-to-end test of install.sh for both targets, in a scratch home. Works on macOS, Linux and Git Bash.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT
export HOME="$TEST_ROOT/home"
export CLAUDE_HOME="$TEST_ROOT/claude"
export CODEX_HOME="$TEST_ROOT/codex"
mkdir -p "$HOME"
export PYTHONUTF8=1

fail() { echo "FAIL: $*" >&2; exit 1; }

# --- help and argument validation ---
bash "$REPO_ROOT/install.sh" --help | grep -q -- "--target" || fail "--help missing usage"
if bash "$REPO_ROOT/install.sh" --target bogus >/dev/null 2>&1; then fail "--target bogus should fail"; fi
if bash "$REPO_ROOT/install.sh" --nope >/dev/null 2>&1; then fail "unknown flag should fail"; fi
test ! -e "$CLAUDE_HOME" || fail "invalid invocations must not install anything"

# --- default target is claude only ---
bash "$REPO_ROOT/install.sh" >/dev/null
test -f "$CLAUDE_HOME/CLAUDE.md" || fail "claude: CLAUDE.md missing"
test -f "$CLAUDE_HOME/skills/zeno/SKILL.md" || fail "claude: zeno skill missing"
test -f "$CLAUDE_HOME/hooks/zeno-session-start.sh" || fail "claude: session hook missing"
test ! -e "$CODEX_HOME" || fail "default target must not touch CODEX_HOME"

# --- codex target ---
bash "$REPO_ROOT/install.sh" --target codex >/dev/null
test -f "$CODEX_HOME/AGENTS.md" || fail "codex: AGENTS.md missing"
test -f "$CODEX_HOME/skills/zeno/SKILL.md" || fail "codex: zeno skill missing"
test -f "$CODEX_HOME/hooks/zeno-session-start.sh" || fail "codex: session hook missing"

# --- a CODEX_HOME that could break out of the hook command's quotes is refused before anything is written ---
# ($ and a backtick are valid in Windows file names; a double quote is not, so that case is Unix-only.)
BAD_HOMES=("$TEST_ROOT"'/we$ird' "$TEST_ROOT"'/we`ird')
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) ;; *) BAD_HOMES+=("$TEST_ROOT"'/we"ird') ;; esac
for BAD_HOME in "${BAD_HOMES[@]}"; do
  if CODEX_HOME="$BAD_HOME" bash "$REPO_ROOT/install.sh" --target codex >/dev/null 2>&1; then fail "unsafe CODEX_HOME should be refused: $BAD_HOME"; fi
  test ! -e "$BAD_HOME" || fail "unsafe CODEX_HOME must not create anything: $BAD_HOME"
done

# --- all targets, twice: idempotent, hooks registered exactly once ---
bash "$REPO_ROOT/install.sh" --target all >/dev/null
bash "$REPO_ROOT/install.sh" --target all >/dev/null

PYBIN=python3
command -v python3 >/dev/null 2>&1 && python3 -c 'import sys' >/dev/null 2>&1 || PYBIN=python
"$PYBIN" - "$CLAUDE_HOME/settings.json" "$CODEX_HOME/hooks.json" <<'PY'
import json, sys
claude, codex = (json.load(open(p))["hooks"] for p in sys.argv[1:3])
def count(entries, marker):
    return sum(marker in h.get("command", "") for e in entries for h in e.get("hooks", []))
assert count(claude["SessionStart"], "zeno-session-start.sh") == 1, "claude SessionStart not exactly once"
assert count(claude["Stop"], "zeno-cost-tracker.sh") == 1, "claude Stop not exactly once"
assert count(codex["SessionStart"], "zeno-session-start.sh") == 1, "codex SessionStart not exactly once"
import glob, os
leftovers = glob.glob(os.path.join(os.path.dirname(sys.argv[1]), ".zeno-tmp-*")) + glob.glob(os.path.join(os.path.dirname(sys.argv[2]), ".zeno-tmp-*"))
assert not leftovers, f"temp files left behind: {leftovers}"
print("hooks registered exactly once")
PY

# --- the installed SessionStart hook runs and emits valid JSON ---
(cd "$TEST_ROOT" && bash "$CLAUDE_HOME/hooks/zeno-session-start.sh" </dev/null | "$PYBIN" -c 'import json,sys; json.load(sys.stdin)') \
  || fail "installed session hook did not emit valid JSON"

echo "install.sh test passed"
