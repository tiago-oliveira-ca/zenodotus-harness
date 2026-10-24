# The `drift.lock` convention

`drift.lock` binds a prose documentation claim to the piece of code it describes, so a change to
that code can be detected as making the doc stale. It is the in-repo, tool-free backstop the
`documenting-code` skill and the `/docs-drift` command maintain. It is modeled on Fiberplane's
`drift` tool but is self-contained — no external binary, no tree-sitter.

## File

- Location: **repo root**, `drift.lock`.
- Format: a JSON array of anchor entries. Commit it with the repo (it is durable, reviewed memory).

```json
[
  {
    "doc": "docs/auth.md#configuration",
    "anchor": "src/auth/provider.ts#AuthConfig",
    "hash": "sha256:9f2b…",
    "updated": "2026-08-04"
  }
]
```

Fields:
- **`doc`** — `"<path>#<section-slug>"`: the Markdown file and the heading whose prose describes the code.
- **`anchor`** — `"<file>#<symbol>"`: the code definition the prose is about (function, class, type,
  endpoint handler, config object).
- **`hash`** — `"sha256:<hex>"` of the **normalized source** of the anchored symbol (see below).
- **`updated`** — ISO date the entry was last reconciled.

## Normalization (before hashing)

Hash the anchored symbol's source after a best-effort **per-line** normalization:
1. Extract the symbol's source span (definition body) — see the note on span extraction below.
2. Strip full-line and trailing comments where the language's comment syntax is known.
3. Per line: **preserve the leading indentation** (it is semantically significant in Python/YAML/
   Makefiles), collapse internal whitespace runs to a single space, and strip trailing whitespace;
   drop blank lines. **Keep the line breaks** — join the surviving lines with `\n`.
4. `sha256` the result; store as `sha256:<hex>`.

**Direction of error — deliberately toward false *positives*.** Do NOT collapse across newlines.
Preserving line structure means an indentation change that alters behavior (e.g. dedenting a
statement out of a Python `if`, or a YAML block change) produces a **different** hash and is caught.
The cost is that a pure line-break reflow can false-*flag* (report drift when nothing behavioral
changed) — that costs only a human glance. The rule: **err toward flagging, never toward a silently
stale doc.**

This is a **heuristic, not an AST hash**, with honest limits:
- **Token-level churn** that leaves behavior unchanged (a trailing comma, reordered arguments, a
  rename) will false-flag. Safe direction (a glance), but noisy on heavily-reformatted code.
- **Comment stripping is language-approximate** — it does nothing for languages whose comment syntax
  isn't recognized, and naïve `#`/`--`/`//` stripping can cut inside string or regex literals
  (`v := "http://x"`). When unsure, hash *without* stripping comments rather than corrupt the source.
- **Span extraction is best-effort without a parser** — locate the definition by its declaration
  line and matching block/`END`, and be consistent run-to-run; if a symbol can't be located
  unambiguously, leave a `TODO(doc-drift:)` rather than hash a guessed span.

For hard guarantees on noisy or large codebases, use the AST-level CI tools below (Fiberplane
`drift` normalizes via tree-sitter) or doctests — recommend, don't bundle.

## How the agent maintains it

- **Bind** — when documenting a code symbol in prose, add (or update) an entry mapping the doc
  section to the symbol, with the current normalized hash.
- **Check** (`/docs-drift`) — for each anchor whose `anchor` file appears in the diff, recompute the
  hash. If it differs from the stored `hash`, the doc is **stale** → flag it. If a changed public
  symbol has no anchor entry, it is **undocumented** → flag it.
- **Reconcile** — after updating the prose (drafted for human review), refresh the entry's `hash` and
  `updated`. Never refresh a hash without actually re-reading the prose against the code.

## When to prefer other layers

`drift.lock` is layer 2 of the drift discipline. Prefer cheaper/stronger layers when they apply:
- **Doctests** (Python `doctest`, Rust doc-tests) for *examples* — self-verifying, no lock file needed.
- **Fiberplane `drift`** (real AST-hash tool, multi-language) — recommend for repos wanting a hard
  CI gate; its `drift.lock` is compatible in spirit.
- **Doc Detective** — for *procedures* (CLI/API/UI steps a doc describes), executed as tests.

Recommend these per repo; do not bundle or install them.
