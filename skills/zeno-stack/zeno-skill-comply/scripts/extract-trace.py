#!/usr/bin/env python3
"""extract-trace.py — turn a session transcript into a tool-call timeline.

Supports both hosts the harness installs to: Claude Code and Codex CLI.

Usage:
  extract-trace.py PROJECT_DIR [--host auto|claude|codex] [--json] [--index N] [--list]
  extract-trace.py --transcript FILE.jsonl [--json]

  PROJECT_DIR   A project's working directory (e.g. the repo a scenario ran in).
  --host        Which host wrote the transcript (default: auto — try Claude, then Codex).
  --transcript  Use an explicit transcript file instead of resolving one (host auto-detected
                from the file's own contents).
  --list        List the matching transcripts (newest first, labelled session/subagent) and exit.
  --scope       Claude only: all (default) | parent | subagents.
  --index N     Use the Nth newest transcript (0 = newest, the default).
  --json        Emit structured JSON instead of the numbered text timeline.

Host layouts (verified against real transcripts — see the note below on what was NOT):
  Claude Code — ~/.claude/projects/<slug>/, where <slug> is the absolute project path with
    every non-alphanumeric character replaced by '-'. Two levels matter:
      <slug>/<session-id>.jsonl                       the parent session
      <slug>/<session-id>/subagents/agent-<id>.jsonl  one per spawned subagent
    Tool calls are `message.content[]` blocks of type `tool_use` ({name, input}).
    (Correction, 2026-08-18: an earlier version of this file claimed both layouts were
    verified against real transcripts. The Codex layout was; the Claude *subagent* layout was
    not — the resolver listed <slug>/ non-recursively and silently missed all 127 subagent
    transcripts present under one project, returning the parent timeline in which each
    scenario is a single opaque `Agent` call. Fixed here; the claim is now accurate.)
  Codex CLI  — $CODEX_HOME/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl. There is no
    path-slug folder, so the project is resolved by reading each rollout's `session_meta`
    line and matching `payload.cwd`. Tool calls are `event_msg` lines whose
    `payload.type == "item_completed"`, carrying `payload.item`:
      CommandExecution -> a shell command (analogous to Claude's Bash)
      FileChange       -> file writes/edits (analogous to Write/Edit)

  NOTE for compliance work: Codex has **no `Skill` tool call**. On Claude, loop engagement is
  visible as `Skill(zeno)`; on Codex the equivalent evidence is a CommandExecution reading a
  SKILL.md, or FileChange creating `.zeno/` cards. Ordering rules written for one host will
  not transfer verbatim to the other.

Output (text): one line per tool call — "  N. ToolName | key=value"
Output (--json): {"transcript": path, "calls": [{"n", "name", "detail", "input"}]}

Why this exists: compliance measurement must read what an agent *did*, not what it
said it did. This script is the deterministic capture step; judging whether the
calls satisfy a spec is meaning-based work for the model, not for a regex here.
"""

import argparse
import json
import os
import sys

# Fields worth surfacing in the compact "detail" column, most informative first.
SALIENT = ["skill", "subagent_type", "file_path", "command", "pattern", "path",
           "description", "url", "prompt"]


def slug_for(project_dir):
    """Claude Code's project-folder slug: absolute path, non-alphanumerics to '-'."""
    abspath = os.path.abspath(os.path.expanduser(project_dir))
    return "".join(c if c.isalnum() else "-" for c in abspath)


def find_transcripts(project_dir, scope="all"):
    """Claude Code transcripts for a project directory, newest first.

    Walks the project folder rather than listing it, because subagent transcripts are nested:
      <slug>/<session-id>.jsonl                          <- the parent session
      <slug>/<session-id>/subagents/agent-<id>.jsonl     <- one per spawned subagent
    A non-recursive listing sees only the parent, in which each spawned scenario appears as a
    single opaque `Agent` tool call — useless for compliance work, whose whole point is to read
    what the subagent actually did. scope: "all" | "parent" | "subagents".
    """
    folder = os.path.join(os.path.expanduser("~/.claude/projects"), slug_for(project_dir))
    if not os.path.isdir(folder):
        return []
    paths = []
    for dirpath, _dirnames, filenames in os.walk(folder):
        for name in filenames:
            if not name.endswith(".jsonl"):
                continue
            full = os.path.join(dirpath, name)
            if scope == "parent" and is_subagent(full):
                continue
            if scope == "subagents" and not is_subagent(full):
                continue
            paths.append(full)
    return sorted(paths, key=os.path.getmtime, reverse=True)


def is_subagent(path):
    """True for a spawned-subagent transcript (lives under a .../subagents/ directory)."""
    return os.sep + "subagents" + os.sep in path


def codex_home():
    return os.path.expanduser(os.environ.get("CODEX_HOME", "~/.codex"))


def find_codex_transcripts(project_dir):
    """Codex rollouts whose session_meta cwd matches project_dir, newest first.

    Codex has no per-project folder, so every rollout's first line is read to find its cwd.
    Only the head of each file is inspected — session_meta is emitted at session start.
    """
    target = os.path.abspath(os.path.expanduser(project_dir))
    root = os.path.join(codex_home(), "sessions")
    hits = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith(".jsonl"):
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, encoding="utf-8") as handle:
                    for _ in range(5):        # session_meta is at the top; do not read the file
                        line = handle.readline()
                        if not line:
                            break
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if rec.get("type") == "session_meta":
                            if os.path.abspath((rec.get("payload") or {}).get("cwd", "")) == target:
                                hits.append(path)
                            break
            except OSError:
                continue
    return sorted(hits, key=os.path.getmtime, reverse=True)


def looks_like_codex(transcript_path):
    """True when the file is a Codex rollout (checked by content, not filename)."""
    try:
        with open(transcript_path, encoding="utf-8") as handle:
            for _ in range(5):
                line = handle.readline()
                if not line:
                    return False
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") in ("session_meta", "event_msg", "response_item"):
                    return True
                if "message" in rec:
                    return False
    except OSError:
        return False
    return False


def codex_timeline(transcript_path):
    """Tool calls from a Codex rollout, in order."""
    calls = []
    with open(transcript_path, encoding="utf-8") as handle:
        for line in handle:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "event_msg":
                continue
            payload = rec.get("payload") or {}
            if payload.get("type") != "item_completed":
                continue
            item = payload.get("item") or {}
            kind = item.get("type")
            if kind == "CommandExecution":
                cmd = item.get("command") or []
                if isinstance(cmd, list):
                    # Codex wraps shell calls as ["/bin/zsh", "-lc", "<script>"]
                    cmd = cmd[-1] if cmd else ""
                inp = {"command": cmd, "cwd": item.get("cwd", ""),
                       "exit_code": item.get("exit_code")}
                detail = f"command={' '.join(str(cmd).split())[:160]}"
            elif kind == "FileChange":
                changed = list((item.get("changes") or {}).keys())
                inp = {"file_path": changed[0] if changed else "",
                       "changes": changed}
                detail = f"file_path={changed[0][:160]}" if changed else "file_path="
            else:
                continue                      # Reasoning/AgentMessage/UserMessage are not tool calls
            calls.append({"n": len(calls) + 1, "name": kind, "detail": detail, "input": inp})
    return calls


def detail_for(inp):
    """One short, human-readable field from a tool-call input."""
    for key in SALIENT:
        value = inp.get(key)
        if isinstance(value, str) and value.strip():
            return f"{key}={' '.join(value.split())[:160]}"
    return json.dumps(inp)[:160] if inp else ""


def timeline(transcript_path):
    """Every tool_use block in the transcript, in order."""
    calls = []
    with open(transcript_path, encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # partial/interleaved lines are normal in a live transcript
            content = (record.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    inp = block.get("input") or {}
                    calls.append({
                        "n": len(calls) + 1,
                        "name": block.get("name", "?"),
                        "detail": detail_for(inp),
                        "input": inp,
                    })
    return calls


def main(argv=None):
    parser = argparse.ArgumentParser(prog="extract-trace.py")
    parser.add_argument("project_dir", nargs="?")
    parser.add_argument("--transcript")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--host", choices=("auto", "claude", "codex"), default="auto")
    parser.add_argument("--scope", choices=("all", "parent", "subagents"), default="all",
                        help="Claude only: which transcripts to consider (default all).")
    parser.add_argument("--json", dest="as_json", action="store_true")
    args = parser.parse_args(argv)

    host = args.host
    if args.transcript:
        path = os.path.expanduser(args.transcript)
        if not os.path.isfile(path):
            print(f"no such transcript: {path}", file=sys.stderr)
            return 2
        if host == "auto":
            host = "codex" if looks_like_codex(path) else "claude"
    else:
        if not args.project_dir:
            parser.error("give a PROJECT_DIR or --transcript")
        found = []
        if host in ("auto", "claude"):
            found = find_transcripts(args.project_dir, args.scope)
            if found:
                host = "claude"
        if not found and host in ("auto", "codex"):
            found = find_codex_transcripts(args.project_dir)
            if found:
                host = "codex"
        if not found:
            print(f"no transcripts for {args.project_dir} "
                  f"(Claude: ~/.claude/projects/{slug_for(args.project_dir)}; "
                  f"Codex: {codex_home()}/sessions/**/rollout-*.jsonl matching that cwd)",
                  file=sys.stderr)
            return 1
        if args.list:
            for i, p in enumerate(found):
                kind = "subagent" if (host == "claude" and is_subagent(p)) else "session "
                print(f"{i}: [{kind}] {p}")
            return 0
        if args.index >= len(found):
            print(f"--index {args.index} out of range ({len(found)} transcripts)", file=sys.stderr)
            return 2
        path = found[args.index]

    calls = codex_timeline(path) if host == "codex" else timeline(path)
    if args.as_json:
        json.dump({"transcript": path, "host": host, "calls": calls}, sys.stdout, indent=1)
        print()
    else:
        print(f"# {path}  [{host}]")
        if not calls:
            print("(no tool calls in this transcript)")
        for call in calls:
            print(f"{call['n']:4d}. {call['name']:14s} | {call['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
