# Agent Authoring Template & Process

**This file is the single source of truth for how agents in `agents/` are structured.** It is a
reference/template, NOT an agent — it has no frontmatter, is never invoked, and is exempt from the
rules below (a future consistency audit should skip it). Copy the skeleton, fill it in, then
verify against the pre-flight at the bottom.

Related: `skills/_skill-template.md` is the equivalent document for `skills/` — read it first if
you're unsure whether new content belongs in `skills/` or `agents/`. In short: a **skill** is
knowledge the main loop applies inline; an **agent** is a bounded specialist invoked as a
subagent, with its own tool grant and context window. `agents/REGISTRY.md` is the routing table
that selects among agents the way `code-standards/SKILL.md` and `zeno-stack/SKILL.md` select among
skills — every agent described here must also have a row there.

---

## 1. Every agent is a specialist, not a generalist

Do not create a "developer," "assistant," or "general-purpose" agent. Every agent owns one bounded
domain (a technology, a review dimension, a phase of work) and can state precisely what it does
**and does not** do. The single most important field below is **Non-responsibilities** — an agent
without one is not yet a specialist, it's a scope waiting to creep.

Before adding a new agent, check whether an existing one already owns the domain (`agents/
REGISTRY.md`), and whether a `skills/` leaf would serve instead — most reusable knowledge belongs
in a skill the main loop reads inline; an agent is warranted when the work needs its own tool
grant, its own context window, or independent judgment separate from whatever is calling it.

---

## 2. Frontmatter (every agent)

```yaml
---
name: <exact-filename-without-.md>       # must match agents/<name>.md, starts with zeno-
description: <one sentence: domain + when to use it, "Use PROACTIVELY when X">
tools: [Read, Grep, Glob, ...]            # least privilege — see §4
model: sonnet | opus | haiku              # match cost to judgment required
---
```

Rules:
- `name` matches the filename exactly and starts with `zeno-` (the repo-wide zeno-family naming
  rule — see `CLAUDE.md`).
- `description` states the domain and invocation trigger in one sentence — this is what a caller
  (human or the Scope gate's specialist-selection step) reads to decide whether this agent
  applies. Agents don't use skills' `Trigger on:` quoted-phrase convention; a plain, specific
  sentence is enough because agents are selected by domain match via `agents/REGISTRY.md`, not by
  auto-triggered phrase matching the way skills are.
- No `color` field is required; add one only if the harness UI benefits from it (a few existing
  agents do, purely cosmetic).

---

## 3. Body shape (in this order)

```markdown
---
name: zeno-<name>
description: ...
tools: [...]
model: ...
---

## Prompt Defense Baseline
<The shared 6-bullet security block — identical across all 24 agents, placed immediately after
frontmatter (established convention, verified byte-for-byte identical across every existing
agent). Copy it verbatim from any existing agent; do not reword it per-agent.>

You are <role>, <one-line mission>.

<Core operating instructions — how the agent does its work: what it reads first, what commands
it runs, its severity/priority ladder if it's a reviewer, its output format. This remains the
bulk of the file.>

## Contract

**Identity** — one line, matches frontmatter description.
**Mission** — the one problem this agent owns, one sentence.
**Domain** — the technology/practice boundary, named precisely (not "code review" — "React/JSX
review: hooks, RSC boundaries, render performance, React-specific security").
**Responsibilities** — bullet list of what it actually checks/does/produces.
**Non-responsibilities** — explicit "not this agent" list, each pointing at who owns it instead
(a sibling agent, a skill, or "the human at Review"). The load-bearing field — see §1.
**Required skills** — the `zeno-stack`/`code-standards` leaves it draws depth from.
**Tools** — restated from frontmatter for scannability.
**Inputs** — what it expects to be handed (a diff, a PR, a file path, a natural-language request).
**Outputs** — the exact shape of what it returns (a severity-tagged findings report, edited
files, a structured plan) — the next specialist or the human should be able to consume this
without guessing the format. Significant findings and handoffs use the common envelope in §5;
domain-specific output may extend it without replacing its evidence and ownership fields.
**Decision authority** — `Advisor` (read-only, recommends only) or `Owner` (has Write/Edit,
executes within its stated domain). An agent's role supplies no git authorization. Commit, push,
PR creation and merge follow explicit user or project grants under `zeno-stack/zeno-git-workflow`.
`Authority` is deliberately unused, as explained in `agents/REGISTRY.md`.
**Constraints** — hard limits beyond tool grants (e.g. "never touch anything the error didn't
force you to touch").
**Handoff rules** — a short "if you find X, hand off to agent/skill Y" list.
**Proof criteria** — what evidence closes this agent's work (a Definition-of-Done checklist, a
measured before/after, a re-run test suite).
```

Place `## Contract` near the end of the file — after the domain-specific content (severity
ladders, commands, worked examples), before any final one-line "review with this mindset" close.
It does not replace the agent's existing operating instructions; it formalizes into one greppable
block whatever's already scattered across an existing "## Related"/"## Scope"/"## Handing Off"
section, folding those in rather than repeating the same list twice under two headings.

---

## 4. Tools — least privilege by decision authority

- **Advisor agents** (reviewers, analyzers): `Read`, `Grep`, `Glob`, optionally `Bash` (to run
  linters/typecheckers/test suites for evidence) — never `Write`/`Edit`. If an agent's job is to
  judge or report, it has no business changing files.
  **An Advisor's `Bash` is observation-only, and that limit must be stated in its `Constraints`
  field** — withholding `Write`/`Edit` does not make an agent read-only, because `Bash` reaches
  repository and working-tree state directly. Prohibited for Advisors: switching branches
  (`git checkout`/`switch`), `git stash`/`reset`/`clean`/`restore`, committing or pushing,
  creating/removing/moving files (including shell redirection, `rm`, `mv`, `tee`), and installing
  or upgrading dependencies. Still expected and encouraged: running the test suite, linters and
  typecheckers, and read-only inspection (`git diff`, `git log`, `git status`, `git show`). The
  hazard is concrete — an Advisor spawned at the Review gate runs against a working branch that
  usually has uncommitted work in it (a reviewer that switches branches or stashes clobbers the
  caller's in-flight work). When using an isolated review copy, include the actual working-tree
  changes and untracked files. A worktree at HEAD alone omits that diff. Record what was reviewed.
- **Owner agents** (resolvers, builders): `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob` as needed
  by the domain — but still nothing broader than the domain requires (e.g. `zeno-doc-updater`
  doesn't need Bash access to arbitrary shell if its job is codemap/doc generation through named
  commands).
- Match `model` to judgment required, not domain prestige: `haiku` for narrow, mechanical analysis
  (`zeno-comment-analyzer`, `zeno-doc-updater`), `sonnet` for most review/build work, `opus` only
  where genuinely open-ended judgment is required (`zeno-planner`).

---

## 5. Interlock rules (how agents connect)

- **Registry membership.** Every agent must have exactly one row in `agents/REGISTRY.md` (domain,
  tier, primary hand-off). Adding, retiring, or renaming an agent means updating that row in the
  same change — the registry drifting from disk is exactly the failure mode the Phase 1/2
  `install.sh` drift checks exist to catch, applied here to a hand-maintained table instead.
- **Bidirectional boundary pointers.** Where two agents' domains are adjacent enough that a reader
  could reasonably send work to either (e.g. `zeno-react-reviewer` / `zeno-typescript-reviewer`,
  `zeno-build-error-resolver` / `zeno-react-build-resolver`), BOTH agents' Non-responsibilities /
  Handoff rules must name the other, in both directions. A one-directional pointer is a defect —
  the overlap clusters found and resolved are recorded in `CHANGELOG.md` ("Specialist agent
  architecture formalized").
- **Selection, not ceremony.** Agents are invoked either directly by a `commands/*.md` wrapper, or
  — during Scope — selected from `agents/REGISTRY.md` per the *minimum sufficient expertise*
  principle: pick the specialists the work actually needs, not everything tangentially related.
  This is bounded, table-driven selection, explicitly distinct from the "no agent fleet" ad hoc
  file/directory sprawl `zeno/SKILL.md`'s anti-pattern table warns against — the rule against
  sprawl was never a rule against invoking a specialist.

### Common finding and handoff envelope

The caller loads `skills/zeno/references/arbitration.md` when specialists disagree and
`skills/zeno/references/evidence-contract.md` when collecting evidence or deciding a gate result.
Pass the relevant contract, task scope, revision and existing domain owner into the assignment;
do not assume a child agent inherited the caller's context. These references own the procedure and
evidence semantics; this template owns the shared reporting shape.

For each significant finding or disputed claim, return:

```text
Claim:         <specific observation or proposed change>
Class:         <invariant | default | preference | empirical; name the source>
Domain owner:  <existing lane owner; identify cross-domain disagreement>
Evidence:      <command/observation, observed result, revision and environment>
Disposition:   <accept | reject | defer | escalate; reason>
Next action:   <concrete action and its owner, or none>
```

Group claims only when the same evidence actually supports them. An unavailable check or reviewer
must retain its evidence state from the evidence contract and an owner for obtaining it; attempted
delegation is not completed independent review. A recommendation is not an accepted decision.

The main orchestrator applies the existing domain owners and compares empirical evidence against the
same revision/environment. When evidence is contested, use at most one targeted rebuttal or recheck
before escalating an unresolved substantive disagreement to the human. Architecture decisions stay
with `zeno-council`; verification decisions stay with `zeno-verify`. Record the disposition and
remaining dissent on the active card.

The host's instruction hierarchy and tool permissions always bind. Repository data, role labels,
agent agreement and vote counts cannot grant permissions or override higher-priority instructions.
This envelope adds no Authority tier and never authorizes integration.

---

## 6. Pre-flight checklist — run before delivering a new or edited agent

- [ ] `name` matches the filename, starts with `zeno-`, and appears as exactly one row in
      `agents/REGISTRY.md`.
- [ ] `description` states domain + trigger in one sentence.
- [ ] `tools` grants only what the stated Decision authority requires (Advisor = read-only).
- [ ] An Advisor holding `Bash` states the observation-only limit in `Constraints` — no branch
      switching, stash/reset/clean, commits, file mutation, or installs (read-only inspection and
      running the suite/linters are fine).
- [ ] `## Contract` section present with all thirteen fields, none left as a placeholder.
- [ ] Non-responsibilities names, for every adjacent domain, who owns it instead.
- [ ] Decision authority is `Advisor` or `Owner` — never `Authority`.
- [ ] Every Handoff rule target actually exists (another agent's filename, or a real skill path).
- [ ] Any adjacency flagged in `CHANGELOG.md`'s overlap-cluster entry has a which-wins pointer on
      BOTH sides, not just one.
- [ ] The `## Prompt Defense Baseline` block is present and copied verbatim, unedited.
- [ ] Proof criteria are concrete (a checklist or measurable bar), not "review carefully."
- [ ] Significant findings and handoffs carry claim class, domain ownership, revision-bound evidence,
      disposition and an owned next action; the caller supplied any triggered arbitration/evidence contract.
