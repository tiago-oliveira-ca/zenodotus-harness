#!/usr/bin/env bash
# End-to-end regression test for ownership-bounded Codex installation.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT
TEST_HOME="$TEST_ROOT/codex"

mkdir -p \
  "$TEST_HOME/skills/.system" \
  "$TEST_HOME/skills/user-skill" \
  "$TEST_HOME/skills/obsolete-skill" \
  "$TEST_HOME/skills/zeno/references" \
  "$TEST_HOME/hooks"

printf 'codex-owned\n' > "$TEST_HOME/skills/.system/keep.txt"
printf 'user-owned\n' > "$TEST_HOME/skills/user-skill/keep.txt"
printf 'obsolete\n' > "$TEST_HOME/skills/obsolete-skill/stale.txt"
printf 'stale nested content\n' > "$TEST_HOME/skills/zeno/references/stale.md"
printf 'zeno\nobsolete-skill\n' > "$TEST_HOME/.zenodotus-managed-skills"
printf '#!/usr/bin/env bash\n' > "$TEST_HOME/hooks/zeno-cost-tracker.sh"

cat > "$TEST_HOME/hooks.json" <<JSON
{
  "hooks": {
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "bash \"$TEST_HOME/hooks/zeno-session-start.sh\""}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "bash \"$TEST_HOME/hooks/zeno-cost-tracker.sh\""}]},
      {"hooks": [{"type": "command", "command": "bash \"$TEST_HOME/hooks/user-stop-hook.sh\""}]}
    ]
  }
}
JSON

CODEX_HOME="$TEST_HOME" "$REPO_ROOT/install-codex.sh"
CODEX_HOME="$TEST_HOME" "$REPO_ROOT/install-codex.sh"

test ! -e "$TEST_HOME/skills/zeno/references/stale.md"
test ! -e "$TEST_HOME/skills/obsolete-skill"
test -f "$TEST_HOME/skills/.system/keep.txt"
test -f "$TEST_HOME/skills/user-skill/keep.txt"
test ! -e "$TEST_HOME/hooks/zeno-cost-tracker.sh"
test -f "$TEST_HOME/hooks/zeno-session-start.sh"

python3 - "$TEST_HOME/hooks.json" <<'PY'
import json
import sys

with open(sys.argv[1]) as hooks_file:
    data = json.load(hooks_file)

commands = [
    hook["command"]
    for entries in data["hooks"].values()
    for entry in entries
    for hook in entry.get("hooks", [])
]
assert sum("zeno-session-start.sh" in command for command in commands) == 1
assert not any("zeno-cost-tracker.sh" in command for command in commands)
assert sum("user-stop-hook.sh" in command for command in commands) == 1
PY

UNSAFE_HOME="$TEST_ROOT/unsafe-codex"
mkdir -p "$UNSAFE_HOME/skills/zeno"
printf 'must survive\n' > "$UNSAFE_HOME/skills/zeno/sentinel.txt"
printf 'zeno\n../escape\n' > "$UNSAFE_HOME/.zenodotus-managed-skills"
if CODEX_HOME="$UNSAFE_HOME" "$REPO_ROOT/install-codex.sh"; then
  echo "unsafe manifest unexpectedly succeeded" >&2
  exit 1
fi
test -f "$UNSAFE_HOME/skills/zeno/sentinel.txt"

echo "Codex installer managed-surface test passed"
