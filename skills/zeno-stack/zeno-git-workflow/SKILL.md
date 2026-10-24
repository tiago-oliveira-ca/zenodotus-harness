---
name: zeno-git-workflow
description: >
  Git workflow patterns for branching strategy, commit conventions, merge vs rebase,
  conflict resolution, releases, and repo hygiene. Use when setting up a project's git
  workflow, writing commit messages or PR descriptions, resolving merge conflicts, cutting
  a release, or onboarding a team to git conventions. Trigger on: "branching strategy",
  "commit message", "merge vs rebase", "resolve conflicts", "gitflow", "trunk-based",
  "github flow", "semantic versioning", "cut a release", "pre-commit hook", "gitignore",
  "squash commits", "force push", "rebase onto main", or any question about how to
  structure git history or collaboration.
---

# Git Workflow Patterns

Choosing and enforcing a git workflow — branching, commits, merges, and releases — so
history stays legible and collaboration doesn't degrade into conflict archaeology.

## Branching Strategies

| Strategy | Team size | Release cadence | Best for |
|---|---|---|---|
| GitHub Flow | Any | Continuous | SaaS, web apps, startups — `main` is always deployable, feature branches merge in via PR |
| Trunk-Based | 5+ experienced | Multiple/day | High-velocity teams with feature flags hiding incomplete work |
| GitFlow | 10+ | Scheduled | Enterprise/regulated — `main` holds releases, `develop` integrates, release/hotfix branches bridge them |

**GitHub Flow** (default recommendation absent a strong reason otherwise): `main` is
protected and always deployable; every change is a short-lived `feature/*` or `fix/*`
branch merged via reviewed PR; deploy immediately after merge.

**Trunk-based**: everyone commits to `main` or branches living 1-2 days max; feature flags
gate incomplete work; CI must pass before merge; requires strong test coverage to be safe.

**GitFlow**: `main` is production-only; `develop` is the integration branch; features branch
from and merge back to `develop`; `release/*` branches cut from `develop` and merge to both
`main` and `develop`; `hotfix/*` branches from `main`, merged to both. Heavier ceremony —
reserve for teams with genuinely scheduled releases, not as a default.

## Commit Messages

Use Conventional Commits: `<type>(<scope>): <subject>`, optional body, optional footer.

| Type | Use for |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Restructuring without behavior change |
| `test` | Adding/updating tests |
| `chore` | Maintenance (deps, tooling) |
| `perf` | Performance improvement |
| `ci` | CI/CD config changes |
| `revert` | Reverting a prior commit |

A good commit message explains *why*, not just *what*:

```
fix(api): retry requests on 503 Service Unavailable

The external API occasionally returns 503 errors during peak hours.
Added exponential backoff retry logic with max 3 attempts.

Closes #123
```

Vague messages (`"fixed stuff"`, `"updates"`, `"WIP"`) are a defect, not a shortcut — they
make `git blame` and changelog generation useless. Enforce a template via
`git config commit.template .gitmessage`.

## Merge vs Rebase

| | Merge | Rebase |
|---|---|---|
| History | Preserves exact history, adds a merge commit | Linear — rewrites commits onto the target |
| Use when | Merging a feature branch into `main`; the branch has been pushed and others may depend on it; multiple people worked on it | Updating a local feature branch with latest `main`; the branch is local-only or you're its sole author |
| Never on | — | Pushed shared branches, protected branches, anything already merged — rebase rewrites history and breaks others' work |

Standard pre-PR rebase:

```bash
git checkout feature/user-auth
git fetch origin
git rebase origin/main
# fix conflicts, confirm tests still pass
git push --force-with-lease origin feature/user-auth   # only if you're the sole contributor
```

`--force-with-lease`, not `--force` — it aborts if the remote moved since your last fetch,
protecting against clobbering someone else's push.

## Conflict Resolution

```bash
git checkout main
git merge feature/user-auth --no-commit --no-ff   # surface conflicts without committing
git status                                          # list conflicted files
```

Resolve by editing out `<<<<<<<` / `=======` / `>>>>>>>` markers, via `git mergetool`, or by
taking one side wholesale (`git checkout --ours|--theirs <path>`), then `git add` + commit.

Prevent conflicts rather than resolve them: keep branches small and short-lived, rebase
onto `main` frequently, communicate before touching widely-shared files, prefer feature
flags over long-lived branches, and review/merge PRs promptly.

## Pull Requests

**Title**: same `<type>(<scope>): <description>` convention as commits.

**Description** should cover What / Why / How / Testing, plus a checklist (tests added,
self-review done, docs updated, no new warnings). Screenshots for UI changes.

**Reviewer checklist**: solves the stated problem, edge cases handled, readable and
maintainable, adequately tested, no security concerns, commit history clean.

**Author checklist**: self-reviewed before requesting review, CI green, PR size reasonable
(<500 lines is a good target), scoped to one feature/fix, description explains the change.

## Branch Naming and Cleanup

```
feature/user-authentication
fix/login-redirect-loop
hotfix/critical-security-patch
release/1.2.0
experiment/new-caching-strategy
```

```bash
git branch --merged main | grep -v "^\*\|main" | xargs -n 1 git branch -d   # clean merged locals
git fetch -p                                                                 # prune stale remote-tracking refs
git push origin --delete feature/user-auth                                  # delete remote branch
```

## Releases

Semantic versioning: `MAJOR.MINOR.PATCH` — major for breaking changes, minor for
backward-compatible features, patch for backward-compatible fixes.

```bash
git tag -a v1.2.0 -m "Release v1.2.0

Features:
- Add user authentication

Fixes:
- Resolve login redirect issue"
git push origin v1.2.0

git log v1.1.0..v1.2.0 --oneline --no-merges   # raw changelog input
```

## Repo Hygiene

Essential config: `pull.rebase = true`, `push.default = current`, `init.defaultBranch =
main`, `diff.algorithm = histogram`. Keep `.gitignore` current for dependencies, build
output, env files, IDE artifacts, and caches — a committed `node_modules/` or `.env` is a
recurring cleanup cost, not a one-time mistake.

Pre-commit and pre-push hooks are cheap insurance: lint/test before commit, scan the staged
diff for secret-shaped strings (`password`, `api_key`, `secret`), block `console.log`
leftovers before push.

## Wiring the Mechanical Quality Gate

`zeno-verify` makes format/lint/typecheck mandatory before any code change can be called
done. A hook makes that survive a skipped checklist — it is the enforcement layer that
doesn't depend on anyone remembering. Set it up once per repo where product code lives:

```bash
# .git/hooks/pre-commit (chmod +x) — or managed by husky / lefthook / pre-commit
#!/bin/sh
set -e
staged=$(git diff --cached --name-only --diff-filter=ACM)
[ -z "$staged" ] && exit 0

# 1. Format + lint ONLY the staged files (whole-repo runs get bypassed for being slow).
#    Collect per-language lists first — `xargs -r` is GNU-only, absent on older BSD/macOS.
js=$(printf '%s\n' "$staged" | grep -E '\.(ts|tsx|js|jsx)$' || true)
py=$(printf '%s\n' "$staged" | grep -E '\.py$' || true)
[ -n "$js" ] && printf '%s\n' "$js" | xargs npx biome check
[ -n "$py" ] && printf '%s\n' "$py" | xargs ruff check
[ -n "$py" ] && printf '%s\n' "$py" | xargs ruff format --check

# 2. Secret-shaped strings in the staged diff, not the working tree
if git diff --cached | grep -qEi '(api[_-]?key|secret|password|token)[[:space:]]*[:=][[:space:]]*.{8,}'; then
  echo "possible secret in staged diff — commit blocked (use --no-verify only deliberately)"
  exit 1
fi

exit 0
```

Rules that decide whether the hook actually helps:

- **Check staged files only, not the whole repo.** A hook that takes 30 seconds gets
  bypassed within a week; one that takes under two seconds survives.
- **Typecheck and the full test suite belong in `pre-push` or CI**, not `pre-commit` — they
  are too slow to gate every commit and their value is per-branch, not per-commit.
- **A hook is a convenience, never the real gate.** `--no-verify` bypasses it, and a fresh
  clone has no hooks at all (`.git/hooks/` is not versioned). CI must run the same checks;
  the hook exists to catch problems *before* the push, not instead of the pipeline.
- **Version the hook definitions, not `.git/hooks/`:** commit a `lefthook.yml`,
  `.pre-commit-config.yaml`, or husky's `.husky/` directory so every clone gets them, with a
  one-line setup step in the README.
- **Match the checks to what `zeno-verify` mandates** so a green hook means the Review gate's
  mechanical steps will also pass — divergent hook and CI checks train people to ignore both.

## Undoing Mistakes

```bash
git reset --soft HEAD~1        # undo last commit, keep changes staged
git reset --hard HEAD~1        # undo last commit, discard changes
git revert HEAD                # undo a commit already pushed to a shared branch
git commit --amend -m "..."    # fix the last commit message (only if not yet pushed/shared)
```

`reset --hard` and `push --force` operate on history others may depend on — confirm the
branch is local-only or solely yours before using either.

## Non-Interactive Partial Staging

When `git add -p` is unavailable (agent/CI environments) and a file's working tree mixes an
intended commit with changes that must not be committed, write the index directly from
synthesized content:

```bash
git show HEAD:<file> > /tmp/staged-content   # start from last committed content
# re-apply ONLY the intended edit to /tmp/staged-content
git update-index --cacheinfo 100644,$(git hash-object -w /tmp/staged-content),<file>
git diff --cached <file>   # must show exactly the intended change
git diff <file>            # must show exactly the unrelated leftover
```

The verification pair is the safety invariant: the staged diff must contain exactly the
intended change, the unstaged diff exactly the leftover — check both before committing. The
working tree is never touched, so live/demo state survives intact.

## Importing a Repo (Vendoring Provenance)

A commit sha only identifies a snapshot when the source worktree is clean. Before copying
another repo's content in:

1. Run `git status` on the source and decide explicitly whether to import HEAD or the working
   tree — importing HEAD when the tree is dirty silently drops real code.
2. Build the copy list from `git ls-files` plus `git ls-files --others --exclude-standard`,
   never a raw directory copy — this respects the source `.gitignore` and keeps secrets and
   build artifacts out.
3. Record provenance in the import note and commit body as the sha alone only for a clean
   tree; otherwise "sha + uncommitted working-tree changes" with a one-line description of
   what was dirty.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Committing directly to `main` | Feature branch + PR, even solo |
| Vague commit messages ("fix", "wip", "update") | Conventional Commits with a "why" in the body |
| `git push --force` on a shared/protected branch | `--force-with-lease` on your own branch only, or `git revert` on shared ones |
| Long-lived feature branches (weeks) | Short-lived branches, rebased onto `main` frequently |
| Giant PRs (1000+ lines) | Split into focused, independently reviewable PRs |
| Committing secrets or generated output (`.env`, `dist/`, `node_modules/`) | Add to `.gitignore`; use env vars / build steps |
| Redefining the branch strategy per-feature | Pick one strategy (table above) and apply it consistently |
| Vendoring another repo with a raw `cp -r` | Copy `git ls-files` + untracked-non-ignored files; record sha + dirty-worktree provenance |
| Whole-repo lint/test in `pre-commit` | Staged files only in pre-commit; slow checks in pre-push/CI, or the hook gets bypassed |
| Treating a pre-commit hook as the quality gate | It's bypassable (`--no-verify`) and absent in fresh clones — CI runs the same checks as the real gate |
| Hook definitions living only in `.git/hooks/` | Version `lefthook.yml`/`.pre-commit-config.yaml`/`.husky/` so every clone gets them |

## Pre-flight checklist — run before delivering any git workflow guidance

- [ ] Branching strategy recommendation matches team size and release cadence, not habit
- [ ] Commit message guidance follows Conventional Commits with a "why" in the body
- [ ] Rebase is only recommended for local/solely-owned branches; merge for shared ones
- [ ] `--force-with-lease` is used instead of `--force` wherever a force-push is suggested
- [ ] PR guidance includes both a reviewer and an author checklist
- [ ] Release guidance ties tags to semantic versioning
- [ ] No instruction risks rewriting or discarding history on a shared/protected branch
- [ ] Any quality-gate hook advice checks staged files only, keeps slow checks in pre-push/CI, versions its config outside `.git/hooks/`, and states that CI — not the hook — is the real gate
