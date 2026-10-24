#!/usr/bin/env bash
# Shared helpers for install.sh and install-codex.sh. Source this file; do not run it.
#
#   detect_os   -> sets ZENO_OS to macos | linux | wsl | gitbash | unknown
#   find_python -> sets PY to a working Python 3 interpreter (python3, python, or the Windows `py`
#                  launcher), or exits with install instructions. Windows ships a `python3` stub that
#                  opens the Store and fails, so every candidate is executed, not just looked up.
#   to_native_path <posix-path> -> a path form the host's native tools understand (Git Bash:
#                  C:/Users/..., elsewhere unchanged).

# Windows Python defaults to the legacy code page (cp1252) for stdout and files; the installers print
# non-ASCII status marks and read UTF-8 skill files, so force UTF-8 for every Python they start.
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

detect_os() {
  case "$(uname -s 2>/dev/null)" in
    Darwin) ZENO_OS=macos ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then ZENO_OS=wsl; else ZENO_OS=linux; fi ;;
    MINGW*|MSYS*|CYGWIN*) ZENO_OS=gitbash ;;
    *) ZENO_OS=unknown ;;
  esac
}

# $1 = minimum minor version of Python 3 (default 8). Codex needs 11 (stdlib tomllib).
find_python() {
  local min="${1:-8}" candidate resolved
  PY=""
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 \
       && "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3, $min) else 1)" >/dev/null 2>&1; then
      PY="$candidate"
      return 0
    fi
  done
  if command -v py >/dev/null 2>&1; then
    resolved="$(py -3 -c "import sys; print(sys.executable)" 2>/dev/null | tr -d '\r')" || resolved=""
    if [ -n "$resolved" ] && command -v cygpath >/dev/null 2>&1; then resolved="$(cygpath -u "$resolved")"; fi
    if [ -n "$resolved" ] && "$resolved" -c "import sys; sys.exit(0 if sys.version_info >= (3, $min) else 1)" >/dev/null 2>&1; then
      PY="$resolved"
      return 0
    fi
  fi
  {
    echo "error: Python 3.$min or newer is required but was not found on PATH."
    case "${ZENO_OS:-unknown}" in
      macos)   echo "  install it with: brew install python" ;;
      linux|wsl) echo "  install it with your package manager, e.g. sudo apt install python3" ;;
      gitbash) echo "  install it from https://www.python.org/downloads/windows/ and tick 'Add python.exe to PATH'," ;
               echo "  then reopen Git Bash. (The Microsoft Store 'python3' alias does not count.)" ;;
      *)       echo "  install Python 3 from https://www.python.org/downloads/" ;;
    esac
  } >&2
  exit 1
}

to_native_path() {
  if [ "${ZENO_OS:-}" = "gitbash" ] && command -v cygpath >/dev/null 2>&1; then
    cygpath -m "$1"
  else
    printf '%s\n' "$1"
  fi
}
