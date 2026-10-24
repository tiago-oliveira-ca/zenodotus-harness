# Contributing

Zenodotus is a personal harness published for others to read, fork and adapt. Issues and pull requests are
welcome, but the author decides what fits the library's single-owner design, so please open an issue before
a large change.

## Ground rules

- **Original content only.** Do not paste third-party skills or prompts. If an idea comes from elsewhere,
  rewrite it and credit it in `NOTICE.md`.
- **One owner per topic.** Before adding a skill, check whether one already covers it. Point to the owner
  instead of restating its rule.
- **New skills** follow `skills/_skill-template.md`: the name starts with `zeno-` (for the zeno family) and
  matches its directory, the `description` has a `Trigger on:` list of quoted phrases and stays under about
  1000 characters, and the file ends with an anti-pattern table and a pre-flight checklist.
- **Nest leaves under a dispatcher** (`code-standards`, `documentation`, `testing`, `zeno-stack`) and add the
  routing-table row and a matching trigger word in the dispatcher's description.
- **Evals.** A skill with behavior worth guarding gets `evals/evals.json` in the house shape: `prompt`,
  `expected_output`, `files`, and a list of plain-string `expectations`.
- **Record the change** with a short entry at the top of `CHANGELOG.md`.

## Checks to run

```sh
bash -n install.sh install-codex.sh hooks/*.sh hooks/codex/*.sh
python3 tools/check_skills.py
python3 -m unittest discover -s tools/codex -p 'test_build_codex.py'
bash tools/codex/test_install_codex.sh
bash tools/test_install.sh
```

The same checks run in CI on every pull request, on Ubuntu, macOS and Windows. Keep scripts portable:
no GNU-only flags, no hard-coded `python3`, and LF line endings (`.gitattributes` enforces them).

## Maintainers: repository settings

`tools/github-settings.sh` applies the repository's settings with the `gh` CLI: merge options, read-only workflow
tokens, SHA-pinned actions only, Dependabot, secret scanning and push protection, private vulnerability reporting,
and rulesets for `main` and `v*` tags. It is idempotent; run it again after any visibility change.

## Pull requests

Keep one logical change per PR, explain why in the description, and say how you verified it. Commit to a
branch, not to `main`.
