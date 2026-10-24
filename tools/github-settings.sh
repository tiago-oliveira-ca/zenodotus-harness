#!/usr/bin/env bash
# Apply this repository's GitHub settings with the `gh` CLI. Idempotent: run it again any time, in particular
# right after switching the repository to public, when several protections become available.
#
#   tools/github-settings.sh [owner/repo]        defaults to the repo of the current directory
#
# Needs: gh (authenticated as a repository admin) and python3. Every step reports ok / skipped; a skipped step
# usually means "not available on this plan while the repo is private" and succeeds on the next run once public.
set -uo pipefail

REPO="${1:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
OK=0; SKIPPED=0

step() {  # step "<description>" <command...>
  local desc="$1"; shift
  local out
  if out="$("$@" 2>&1)"; then
    echo "  ok       $desc"; OK=$((OK + 1))
  else
    echo "  skipped  $desc -- $(echo "$out" | tr '\n' ' ' | cut -c1-140)"; SKIPPED=$((SKIPPED + 1))
  fi
}
api() { gh api -H "Accept: application/vnd.github+json" "$@" >/dev/null; }

echo "GitHub settings for $REPO"

echo "Repository"
step "features: issues on; wiki, projects, discussions off" \
  api -X PATCH "repos/$REPO" -F has_issues=true -F has_wiki=false -F has_projects=false -F has_discussions=false
step "merging: merge commit + squash, no rebase, delete branch on merge, offer 'update branch'" \
  api -X PATCH "repos/$REPO" -F allow_merge_commit=true -F allow_squash_merge=true -F allow_rebase_merge=false \
    -F allow_auto_merge=false -F delete_branch_on_merge=true -F allow_update_branch=true
step "topics" \
  api -X PUT "repos/$REPO/topics" -f 'names[]=claude-code' -f 'names[]=codex' -f 'names[]=agent-skills' \
    -f 'names[]=ai-coding' -f 'names[]=llm' -f 'names[]=tdd' -f 'names[]=ddd'

echo "Actions"
step "only GitHub-owned actions, and every action must be pinned to a commit SHA" \
  api -X PUT "repos/$REPO/actions/permissions" -F enabled=true -f allowed_actions=selected -F sha_pinning_required=true
step "selected actions: GitHub-owned only" \
  api -X PUT "repos/$REPO/actions/permissions/selected-actions" -F github_owned_allowed=true \
    -F verified_creators_allowed=false
step "workflow token is read-only and cannot approve pull requests" \
  api -X PUT "repos/$REPO/actions/permissions/workflow" -f default_workflow_permissions=read \
    -F can_approve_pull_request_reviews=false
step "workflows from outside contributors need approval" \
  api -X PUT "repos/$REPO/actions/permissions/fork-pr-contributor-approval" -f approval_policy=all_external_contributors

echo "Security"
step "Dependabot alerts" api -X PUT "repos/$REPO/vulnerability-alerts"
step "Dependabot security updates" api -X PUT "repos/$REPO/automated-security-fixes"
step "secret scanning and push protection" \
  api -X PATCH "repos/$REPO" \
    -f 'security_and_analysis[secret_scanning][status]=enabled' \
    -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled'
step "private vulnerability reporting" api -X PUT "repos/$REPO/private-vulnerability-reporting"

# --- rulesets: create, or update the one with the same name ---
ruleset() {  # ruleset <name> <json-file>
  local name="$1" file="$2" id
  id="$(gh api "repos/$REPO/rulesets" --jq ".[] | select(.name == \"$name\") | .id" 2>/dev/null | head -1)" || true
  if [ -n "$id" ]; then
    api -X PUT "repos/$REPO/rulesets/$id" --input "$file"
  else
    api -X POST "repos/$REPO/rulesets" --input "$file"
  fi
}

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cat > "$TMP/main.json" <<'JSON'
{
  "name": "protect main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "bypass_actors": [ { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "pull_request" } ],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true } },
    { "type": "required_status_checks", "parameters": {
        "strict_required_status_checks_policy": false,
        "required_status_checks": [
          { "context": "checks (ubuntu-latest)" },
          { "context": "checks (macos-latest)" },
          { "context": "checks (windows-latest)" } ] } }
  ]
}
JSON
cat > "$TMP/tags.json" <<'JSON'
{
  "name": "protect release tags",
  "target": "tag",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/tags/v*"], "exclude": [] } },
  "rules": [ { "type": "deletion" }, { "type": "non_fast_forward" }, { "type": "update" } ]
}
JSON
echo "Rulesets"
step "main: no deletion or force push; pull request with passing CI on three OSes; owner may bypass via PR" \
  ruleset "protect main" "$TMP/main.json"
step "release tags v*: cannot be moved or deleted" ruleset "protect release tags" "$TMP/tags.json"

echo
echo "$OK applied, $SKIPPED skipped."
[ "$SKIPPED" -eq 0 ] || echo "Skipped steps normally need the repository to be public (or a paid plan). Re-run this script after switching visibility."
echo "Manual, account-level (cannot be set from a repository): enable 2FA, keep your email private, and turn on"
echo "'Block command line pushes that expose my email' under Settings > Emails."
