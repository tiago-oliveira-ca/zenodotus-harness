# Security policy

## Reporting a vulnerability

Please report security issues privately through GitHub: **Security → Report a vulnerability** on this
repository (private vulnerability reporting). Do not open a public issue for something exploitable.

Include what you found, how to reproduce it, and which file or script is affected. Expect an
acknowledgement within a week; this is a one-person project, so fixes are best effort.

## What is in scope

Zenodotus is configuration, not a service, but it does run code on your machine:

- `install.sh` and `install-codex.sh` copy files into `~/.claude` and `~/.codex` and edit
  `~/.claude/settings.json` and the Codex hook config.
- `hooks/*.sh` run on SessionStart and Stop events, and read the repo's `.zeno/project.md`.
- `tools/codex/build_codex.py` deletes and regenerates an output directory.
- Skills, agents and commands are prompts that steer an agent with shell and file access.

Reports about unsafe deletes, path traversal, command injection through repository content, or a skill
that tells an agent to bypass its own permission checks are all welcome.

## Before you install

Read what `install.sh` does and review the hooks. Run `./install-codex.sh --dry-run --out <dir>` to
preview the Codex output. `install.sh` replaces `~/.claude/CLAUDE.md` after saving a dated backup.
