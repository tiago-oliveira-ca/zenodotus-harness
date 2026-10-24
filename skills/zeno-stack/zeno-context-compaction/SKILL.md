---
name: zeno-context-compaction
description: >
  Rubric for compacting a long session without losing the work. Sorts context into KEEP, COMPRESS
  and DROP, lists what is never dropped, preserves exact values verbatim, detects state already
  durable in `.zeno/` cards, ADRs or Jira so it is pointed to instead of copied, orders what to keep
  by priority, and writes a Task-State summary (goal, decisions, open items, next step). Use it as the
  instruction text for `/compact`, or when summarizing or handing off a session. Trigger on:
  "compact", "/compact", "context is full", "summarize this session", "handoff", "what should I keep",
  "context window".
---

# Zeno Context Compaction — keep the task, drop the transcript

Compaction replaces a long conversation with a summary. What the summary omits is gone. Use this rubric
to decide what survives, whether the summary is written by you or you are drafting the text for
`/compact <instructions>`.

**Iron Law: A COMPACTION MAY SHRINK THE STORY OF THE WORK, NEVER THE STATE OF THE WORK.** The goal,
decisions, open items, exact values and next step must survive. Chat narration may not.

## What Claude Code does for you (verified against the docs)

- Project-root `CLAUDE.md` is re-read from disk and re-injected after compaction. Rules written there
  survive; rules that exist only in conversation do not. Put durable rules in `CLAUDE.md` or a `.zeno/` card.
- The zeno SessionStart hook also fires after compaction and restores the zeno mandate plus the active
  thread's Goal, Next step and branch from `.zeno/project.md`. Keep those two lines current.
- Nothing documented lets a `CLAUDE.md` section steer the summarizer, so pass this rubric through
  `/compact <instructions>` when you want it applied.

## KEEP — verbatim or near-verbatim

- The goal and the acceptance criteria being worked to.
- Decisions made, with the reason and the rejected option.
- Open questions, blockers and unmet assumptions, each with its owner.
- Exact values (below).
- Failing tests and the command that shows them failing.
- The next step, stated as an action someone can start without asking.

## COMPRESS — one line each

- Exploration that reached a conclusion: keep the conclusion and where the evidence lives.
- Tool output already acted on: keep the verdict and the path, not the dump.
- Approaches tried and abandoned: one line stating why.
- Long discussion that ended in a decision: keep the decision.

## DROP

- Greetings, status chatter, restated plans, progress narration.
- Repeated file contents and command output that can be re-run or re-read.
- Superseded drafts, dead ends with no lesson, resolved questions with no remaining consequence.

## Never drop

- The user's explicit instructions, constraints and approvals (and refusals).
- Authorization state: what was approved, what is still waiting for approval.
- Destructive or irreversible actions already taken, or explicitly forbidden.
- The current branch, working-tree state and unmerged or unpushed work.
- Unresolved errors and the evidence behind them.
- Anything the user said to remember.

## Preserve exact values

Copy these character-for-character, never paraphrase: file paths, branch names, commit hashes, PR and
issue numbers, command lines, error messages, identifiers and keys, version numbers, URLs, thresholds
and numeric limits, and quoted user wording that sets a requirement. A summary that says "the config
file" instead of the path forces the next session to search again.

## Durable state detection — point, don't copy

Before writing a fact into the summary, ask whether it already lives somewhere that survives:

| Fact | Durable home | In the summary |
|---|---|---|
| Scope, acceptance criteria, Task list, decisions, proof | `.zeno/` card | Path of the card |
| Architecture decision | ADR | ADR number |
| Requirement, ticket status | Jira / GitHub issue | Key or number |
| Code and tests | git history | Branch and commit hash |
| Standing rule | `CLAUDE.md` / `AGENTS.md` | Nothing (it is re-injected) |

If the durable copy is stale, update it first, then point to it. If a fact has no durable home and the
loss would hurt, either give it one (append to the card) or keep it in the summary.

## Compaction priority

When space is tight, keep in this order and cut from the bottom:

1. Instructions, approvals and constraints
2. Current goal and the next step
3. Decisions and open items
4. Exact values and failing evidence
5. Conclusions of exploration
6. Narrative of how you got here

## Recency is not enough

The last twenty messages are not automatically the important ones. Do not keep a message because it is
recent, and do not drop one because it is old: a constraint stated at the start still binds, and a
long debugging tangent at the end may reduce to one line. Judge by the priority list, not by position.

## Task-State Model — the shape of the summary

```
Goal:            <one sentence, plus acceptance criteria or a card path>
Branch/State:    <branch, commit, clean or dirty, PR number and state>
Done:            <what is finished, each with its proof or path>
Decisions:       <decision — reason — rejected option>
Open:            <questions, blockers, assumptions, who decides>
Constraints:     <user instructions, approvals, forbidden actions>
Exact values:    <paths, hashes, commands, errors, numbers>
Next step:       <the first action, concrete>
Durable at:      <card, ADR, issue links>
```

Fill every line, writing `none` where empty so a missing line cannot hide a missing fact.

## Open issues and gaps

Record in the summary any claim you could not verify and any input that was missing from the request, so
the next session knows what is guessed rather than known.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Summarizing the conversation chronologically | Write the Task-State Model |
| Keeping the last N messages because they are recent | Rank by the priority list |
| "The config file", "the earlier PR" | Exact path, exact number |
| Copying a card's content into the summary | Point to the card path |
| Dropping an approval or a refusal as chatter | Authorization state is never dropped |
| Compacting with a dirty tree and no record of it | Commit or record branch and state first |
| Assuming a `CLAUDE.md` section steers the summarizer | Pass the rubric through `/compact <instructions>` |
| Leaving the next step vague | A concrete first action |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "I'll remember the details" | After compaction only the summary and re-injected files exist |
| "It's in the transcript" | The transcript is what compaction removes |
| "Short summary is better" | Short is good only after the state lines are complete |
| "The user said it recently so it's kept" | Recency is not a retention rule |

## Red flags — stop, you're about to lose state

- A path, hash, PR number or command is paraphrased.
- The summary has no Next step or no Constraints line.
- An approval or a refusal is missing.
- Uncommitted work exists and the summary does not say so.
- A fact is copied from a card that is stale.

## Pre-flight checklist — run before compacting or handing off

- [ ] Goal, constraints and approvals are present and exact.
- [ ] Branch, commit and tree state are stated.
- [ ] Every path, hash, number, command and error is verbatim.
- [ ] Durable facts point to their card, ADR or issue, and those are current.
- [ ] Decisions carry their reason and the rejected option.
- [ ] Open items and unverified claims are listed.
- [ ] Next step is a concrete first action.
- [ ] Every Task-State line is filled, or says `none`.
