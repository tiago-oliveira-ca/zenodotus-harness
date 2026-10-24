## What and why

<!-- One logical change per PR. Say why, not only what. -->

## How I verified it

<!-- Commands you ran and what you observed. -->

## Checklist

- [ ] `bash -n` on shell scripts, `python3 tools/check_skills.py`, the Codex tests and `bash tools/test_install.sh` pass
- [ ] Original content only: nothing pasted from another project
- [ ] New or changed skills follow `skills/_skill-template.md` (and keep the description under ~1000 characters)
- [ ] `CHANGELOG.md` has an entry; docs that mention the change are updated
- [ ] Scripts stay portable (macOS, Linux, Git Bash): no GNU-only flags, no hard-coded `python3`
