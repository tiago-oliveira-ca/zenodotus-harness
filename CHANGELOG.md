# Changelog

All notable changes to Zenodotus, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This repository starts from a single squashed commit,
so earlier history is not listed.

## 2026-10-24

### Added
- **Cross-platform installer.** `install.sh` now installs Claude Code, Codex CLI or both:
  `--target claude|codex|all` (default `claude`), `--help`, and anything after `--` goes to `install-codex.sh`.
  It runs on macOS, Linux, WSL and Git Bash.
- **`install.ps1`**, a PowerShell launcher that finds Git Bash (skipping the WSL launcher in `System32`) and
  delegates to `install.sh`, so Windows and Unix cannot drift apart.
- **`tools/install-common.sh`**: OS detection and a Python finder that executes each candidate (`python3`,
  `python`, the `py` launcher) instead of trusting `PATH`, so the Windows Store stub is skipped. Claude needs
  Python 3.8+, Codex 3.11+; a missing Python fails early with per-OS advice. The hooks resolve Python the same way.
- **`tools/test_install.sh`**: argument validation, target isolation, both targets, idempotence, hooks registered
  exactly once, and a valid hook payload. CI runs it on Ubuntu, macOS and Windows, plus the PowerShell launcher.
- **`.gitattributes`** forces LF endings on shell scripts so a Windows checkout cannot break `bash install.sh`.
- **Context compaction skill**, `zeno-stack/zeno-context-compaction`: a keep / compress / drop rubric for `/compact`
  and session handoff. It never drops instructions, approvals, irreversible actions or branch state, keeps exact
  values verbatim, points to durable records (`.zeno/` cards, ADRs, issues) instead of copying them, and ends in a
  Task-State summary. Claude Code re-injects project-root `CLAUDE.md` after `/compact` but documents no way for a
  `CLAUDE.md` section to steer the summarizer, so the rubric is passed through `/compact <instructions>`.
- **Repository setup for going public**: `CODE_OF_CONDUCT.md`, issue forms, a pull request template,
  `CODEOWNERS`, Dependabot for the pinned Actions, a CodeQL workflow (Python and Actions), and
  `tools/github-settings.sh`, an idempotent script that applies the repository settings with `gh`: merge options,
  a read-only workflow token, GitHub-owned actions only and pinned to SHAs, approval for outside contributors'
  workflows, Dependabot alerts and updates, secret scanning, push protection, private vulnerability reporting, and
  rulesets protecting `main` (pull request, passing CI on three OSes, no force push or deletion) and `v*` tags.

### Changed
- `README.md` rewritten (requirements per OS, install, Windows notes, layout, checks); `USAGE.md`, `AGENTS.md`,
  `CLAUDE.md`, `CONTRIBUTING.md` and `SECURITY.md` updated to match.
- `install-codex.sh` writes the registered hook path in native form on Git Bash.
- `settings.json` and `hooks.json` are written atomically (temp file plus rename, file mode preserved).
- CI actions are pinned to commit SHAs.
- Removed `docs/changelog-archive.md`, `docs/proposals/` and `NOTICE.md`; the older entries are gone with the archive.

### Fixed
- Windows: `build_codex.py` read skill files in the console code page (cp1252) and crashed on UTF-8 content, and
  the installer's `✓` status marks crashed the same way. Every read and write now names UTF-8 and writes LF, and
  the installers force UTF-8 for the Python they start.

### Security
- Both SessionStart hooks no longer copy text from `.zeno/project.md` into the session. A cloned repository could
  plant instructions in its Goal or Next-step lines. The hook now says only that a thread exists and points to
  `/zeno resume`; the branch name is sanitized to `[A-Za-z0-9._/-]` and capped at 100 characters.
- `install-codex.sh` refuses a `CODEX_HOME` containing `"`, `$`, a backtick, a backslash or a newline, because the
  path is embedded in a hook command that Codex later runs through a shell.
- `graphify` installs a pinned `graphifyy==0.9.95` and no longer falls back to `--break-system-packages`;
  `agent-browser` is pinned to `0.39.2`.
- The CircleCI template downloads a pinned release and verifies its checksum instead of piping a script into
  `sudo bash`.
- The build-resolver skill and agent use `npm ci` and no longer delete `package-lock.json`.

## 2026-10-23

### Added
- **Architecture Council**: new method skill `zeno-council`, run first at Scope, before `zeno-insight`. Eight
  inline roles (Chief Architect, Business/Domain, Application, Data, Platform/Cloud, Security, SRE, Challenger)
  question before they design. *Lite* depth (one line on the card, no questions) is for work that adds no new
  boundary, data store, integration, sensitive data, security posture or non-functional requirement. *Full* depth
  asks up to 7 questions per round (`❓` with a recommended `➡️` default), stops for answers, then gives 2-3
  options, a debate with an adversarial Challenger, a trade-off table, and a recommendation with rejected
  alternatives and revisit triggers. Wired into `zeno`, `zeno-insight`, `zeno-ddd`, the registry, `CLAUDE.md`,
  `AGENTS.md`, `/zeno` and both SessionStart hooks. The roles are personas, not new agents.
- **Jira structure review**, `zeno-stack/zeno-jira-structure-review`: reviews an Epic / Story / Task / Bug /
  Sub-task hierarchy and proposes a corrected one in a fixed report. It applies only safe edits; structural changes
  need approval each time and nothing is deleted without explicit authorization. It works from a pasted export until
  the Atlassian MCP is authenticated. Planning standards' "Task" (a step inside a Story) maps to a Jira Sub-task, and
  this skill wins on Jira issue types and parents.
- **Implementation guardrails**, `zeno-stack/zeno-implementation-guardrails`, loaded during Execution: a
  source-of-truth ranking (user, Jira issue, accepted ADRs, architecture docs, repo instructions, code conventions,
  own judgment) and three tripwires: `ARCHITECTURE IMPACT DETECTED` with an `ADR PROPOSAL`, `DATA MIGRATION RISK`,
  and `BREAKING API CHANGE`. It also adds test-integrity rules and a dependency checklist, and points to the owning
  skill for everything else.

### Changed
- The council stops only on **blocking** unknowns: ones where a plausible answer would change which option wins, or
  add a hard requirement (compliance scope, sensitive or regulated data, an irreversible or destructive choice, a new
  external runtime dependency). Everything else becomes a recorded assumption with a default and a revisit condition.
  When a request says the requirements are settled, the council goes straight to options, but never assumes
  sensitive-data handling or a destructive operation. The definition lives only in `zeno-council`; `zeno` and the
  hooks point to it.
- Skill discovery: lane rows for the Jira and guardrails skills in `CLAUDE.md` and `AGENTS.md`, because a leaf behind
  a dispatcher was not found unprompted.

### Fixed
- Eval fixtures for the council, Jira and guardrails suites: they used `assertions` where the house shape reads
  `expectations`; one prompt claimed settled requirements without giving any; one pasted nothing; two assertions were
  too loose.

## 2026-09-04

### Fixed
- `install-codex.sh` replaces generated top-level skill directories exactly and records their names in
  `$CODEX_HOME/.zenodotus-managed-skills`, so obsolete managed content is removed without touching Codex's own
  `.system` or unrelated user skills. It also removes stale Zenodotus hook scripts and their exact registrations.
- The Codex generator rejects output paths that overlap the source repository or the active Codex installation,
  overwrites an existing directory only if it carries its ownership marker, and treats a missing fold target as a
  fatal error.
