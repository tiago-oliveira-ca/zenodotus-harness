---
description: "Create a GitHub PR from current branch with unpushed commits — discovers templates, analyzes changes, pushes"
argument-hint: "[base-branch] (default: main)"
---

# /pr

**Input**: `$ARGUMENTS` — optional; may contain a base branch name and/or flags (e.g. `--draft`).

**Parsing `$ARGUMENTS`**:
- Pull out any recognized flag (`--draft`).
- Whatever non-flag text remains is treated as the base branch name.
- If no base branch was given, default to `main`.

---

## Phase 1 — validate

Check that a PR actually makes sense here:

```bash
git branch --show-current
git status --short
git log origin/<base>..HEAD --oneline
```

| Check | Passes when | If it fails |
|---|---|---|
| Not on the base branch | current branch ≠ base | Stop: "Switch to a feature branch first." |
| Working directory clean | no uncommitted changes | Warn: "You have uncommitted changes. Commit or stash first." |
| Commits ahead exist | `git log origin/<base>..HEAD` is non-empty | Stop: "No commits ahead of `<base>`. Nothing to PR." |
| No PR already open | `gh pr list --head <branch> --json number` is empty | Stop: "PR already exists: #<number>. Use `gh pr view <number> --web` to open it." |

Only continue once every check clears.

---

## Phase 2 — discover

### PR template

Look for a template, in this order:

1. `.github/PULL_REQUEST_TEMPLATE/` — if this directory exists, list its files and let the user
   pick one (or fall back to `default.md`).
2. `.github/PULL_REQUEST_TEMPLATE.md`
3. `.github/pull_request_template.md`
4. `docs/pull_request_template.md`

If one is found, read it and build the PR body around its structure.

### Commit analysis

```bash
git log origin/<base>..HEAD --format="%h %s" --reverse
```

Use the commit history to derive:
- **Title** — conventional-commit style with a type prefix (`feat: ...`, `fix: ...`, etc.). If the
  branch mixes types, use whichever dominates; if there's a single commit, use its message as-is.
- **Summary** — commits grouped by type/area.

### File analysis

```bash
git diff origin/<base>..HEAD --stat
git diff origin/<base>..HEAD --name-only
```

Bucket the changed files into source, tests, docs, config, migrations.

### Planning artifacts

Check whether this PR traces back to a card on `.zeno/project.md`'s Kanban board: read
`.zeno/project.md` and find the Epic/Feature/Story/Task/SubTask card (under `.zeno/docs/`) whose
Stage/Status matches the work this branch closes out.

Link that card's path in the PR body, along with its Proof entry if the card has already closed.

---

## Phase 3 — push

```bash
git push -u origin HEAD
```

If the push is rejected for having diverged:
```bash
git fetch origin
git rebase origin/<base>
git push -u origin HEAD
```

If the rebase hits conflicts, stop and surface them to the user rather than resolving blind.

---

## Phase 4 — create

### With a template

Fill each section of the discovered template using the commit and file analysis from Phase 2.
Keep every section from the template — mark a section "N/A" if it doesn't apply rather than
dropping it.

### Without a template

Fall back to this shape:

```markdown
## Summary

<1-2 sentence description of what this PR does and why>

## Changes

<bulleted list of changes grouped by area>

## Files Changed

<table or list of changed files with change type: Added/Modified/Deleted>

## Testing

<description of how changes were tested, or "Needs testing">

## Related Issues

<linked issues with Closes/Fixes/Relates to #N, or "None">
```

### Create it

```bash
gh pr create \
  --title "<PR title>" \
  --base <base-branch> \
  --body "<PR body>"
  # Add --draft if the --draft flag was parsed from $ARGUMENTS
```

---

## Phase 5 — verify

```bash
gh pr view --json number,url,title,state,baseRefName,headRefName,additions,deletions,changedFiles
gh pr checks --json name,status,conclusion 2>/dev/null || true
```

---

## Phase 6 — report

```
PR #<number>: <title>
URL: <url>
Branch: <head> → <base>
Changes: +<additions> -<deletions> across <changedFiles> files

CI Checks: <status summary or "pending" or "none configured">

Artifacts referenced:
  - <closing .zeno/ card, if any, linked in PR body>

Next steps:
  - gh pr view <number> --web   → open in browser
  - /code-review <number>       → review the PR
  - gh pr merge <number>        → merge when ready
```

---

## Edge cases

- **`gh` not installed**: stop with "GitHub CLI (`gh`) is required. Install: <https://cli.github.com/>"
- **Not authenticated**: stop with "Run `gh auth login` first."
- **Force push needed**: after a rebase against a diverged remote, use
  `git push --force-with-lease` — never a bare `--force`.
- **Multiple PR templates**: if `.github/PULL_REQUEST_TEMPLATE/` holds more than one file, list
  them and ask the user which to use.
- **Large PR (20+ files)**: warn about the size and suggest splitting it if the changes are
  logically separable.
