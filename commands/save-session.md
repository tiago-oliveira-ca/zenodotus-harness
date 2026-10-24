---
description: Save current session state to a dated file in ~/.claude/session-data/ so work can be resumed in a future session with full context.
---

# /save-session

> **Contract owner:** the `zeno-stack/zeno-sessions` skill defines this lane's shared contract — filename convention, section format, alias store, and the prefer-`.zeno/`-when-tracked rule. The three session commands implement that contract; on a conflict, the skill wins.

Writes down what happened in this session — what got built, what worked, what didn't, what's left — into a dated file so a future session can pick up exactly where this one stopped.

## When to run it

- Before closing out a work session
- Before hitting context limits (save first, then start fresh)
- Right after solving something gnarly you'll want to remember
- Any time you need to hand context off to a future session

## Process

### Step 1 — gather the context

Before writing anything, collect:

- every file touched this session (via `git diff`, or recalled from the conversation)
- what was discussed, tried, and decided
- any errors hit, and how (or whether) they got resolved
- current test/build status, if relevant

### Step 2 — make sure the sessions folder exists

The canonical store lives in the user's Claude home directory:

```bash
mkdir -p ~/.claude/session-data
```

### Step 3 — write the session file

Create `~/.claude/session-data/YYYY-MM-DD-<short-id>-session.tmp`, using today's real date and a short-id that follows this convention (kept consistent with `/sessions`, which lists and parses these same filenames):

- allowed characters: letters `a-z`/`A-Z`, digits `0-9`, hyphens `-`, underscores `_`
- minimum length: 1 character
- recommended for new files: lowercase letters, digits, and hyphens, 8+ characters, to avoid same-day collisions

Valid: `abc123de`, `a1b2c3d4`, `frontend-worktree-1`, `ChezMoi_2`
Avoid for new files: `A`, `test_id1`, `ABC123de`

Full example: `2024-01-15-abc123de-session.tmp`

The legacy `YYYY-MM-DD-session.tmp` form (no short-id) still works for reads, but new files should use the short-id form to avoid collisions.

### Step 4 — fill in every section below

Write each section honestly. Don't skip one — write "Nothing yet" or "N/A" if there's genuinely nothing to say. A section left out entirely is worse than one that's honestly empty.

### Step 5 — show the user what got written

After writing the file, print its full contents and ask:

```
Session saved to [actual resolved path to the session file]

Does this look accurate? Anything to correct or add before we close?
```

Wait for confirmation, and make edits if asked.

---

## Session file format

```markdown
# Session: YYYY-MM-DD

**Started:** [approximate time if known]
**Last Updated:** [current time]
**Project:** [project name or path]
**Topic:** [one-line summary of what this session was about]

---

## What We Are Building

[1-3 paragraphs describing the feature, bug fix, or task. Include enough
context that someone with zero memory of this session can understand the goal.
Include: what it does, why it's needed, how it fits into the larger system.]

---

## What WORKED (with evidence)

[List only things that are confirmed working. For each item include WHY you
know it works — test passed, ran in browser, Postman returned 200, etc.
Without evidence, move it to "Not Tried Yet" instead.]

- **[thing that works]** — confirmed by: [specific evidence]
- **[thing that works]** — confirmed by: [specific evidence]

If nothing is confirmed working yet: "Nothing confirmed working yet — all approaches still in progress or untested."

---

## What Did NOT Work (and why)

[This is the most important section. List every approach tried that failed.
For each failure write the EXACT reason so the next session doesn't retry it.
Be specific: "threw X error because Y" is useful. "didn't work" is not.]

- **[approach tried]** — failed because: [exact reason / error message]
- **[approach tried]** — failed because: [exact reason / error message]

If nothing failed: "No failed approaches yet."

---

## What Has NOT Been Tried Yet

[Approaches that seem promising but haven't been attempted. Ideas from the
conversation. Alternative solutions worth exploring. Be specific enough that
the next session knows exactly what to try.]

- [approach / idea]
- [approach / idea]

If nothing is queued: "No specific untried approaches identified."

---

## Current State of Files

[Every file touched this session. Be precise about what state each file is in.]

| File              | Status         | Notes                      |
| ----------------- | -------------- | --------------------------- |
| `path/to/file.ts` | PASS: Complete    | [what it does]             |
| `path/to/file.ts` |  In Progress | [what's done, what's left] |
| `path/to/file.ts` | FAIL: Broken      | [what's wrong]             |
| `path/to/file.ts` |  Not Started | [planned but not touched]  |

If no files were touched: "No files modified this session."

---

## Decisions Made

[Architecture choices, tradeoffs accepted, approaches chosen and why.
These prevent the next session from relitigating settled decisions.]

- **[decision]** — reason: [why this was chosen over alternatives]

If no significant decisions: "No major decisions made this session."

---

## Blockers & Open Questions

[Anything unresolved that the next session needs to address or investigate.
Questions that came up but weren't answered. External dependencies waiting on.]

- [blocker / open question]

If none: "No active blockers."

---

## Exact Next Step

[If known: The single most important thing to do when resuming. Be precise
enough that resuming requires zero thinking about where to start.]

[If not known: "Next step not determined — review 'What Has NOT Been Tried Yet'
and 'Blockers' sections to decide on direction before starting."]

---

## Environment & Setup Notes

[Only fill this if relevant — commands needed to run the project, env vars
required, services that need to be running, etc. Skip if standard setup.]

[If none: omit this section entirely.]
```

---

## Worked example

```markdown
# Session: 2024-01-15

**Started:** ~2pm
**Last Updated:** 5:30pm
**Project:** my-app
**Topic:** Building JWT authentication with httpOnly cookies

---

## What We Are Building

User authentication system for the Next.js app. Users register with email/password,
receive a JWT stored in an httpOnly cookie (not localStorage), and protected routes
check for a valid token via middleware. The goal is session persistence across browser
refreshes without exposing the token to JavaScript.

---

## What WORKED (with evidence)

- **`/api/auth/register` endpoint** — confirmed by: Postman POST returns 200 with user
  object, row visible in Supabase dashboard, bcrypt hash stored correctly
- **JWT generation in `lib/auth.ts`** — confirmed by: unit test passes
  (`npm test -- auth.test.ts`), decoded token at jwt.io shows correct payload
- **Password hashing** — confirmed by: `bcrypt.compare()` returns true in test

---

## What Did NOT Work (and why)

- **Next-Auth library** — failed because: conflicts with our custom Prisma adapter,
  threw "Cannot use adapter with credentials provider in this configuration" on every
  request. Not worth debugging — too opinionated for our setup.
- **Storing JWT in localStorage** — failed because: SSR renders happen before
  localStorage is available, caused React hydration mismatch error on every page load.
  This approach is fundamentally incompatible with Next.js SSR.

---

## What Has NOT Been Tried Yet

- Store JWT as httpOnly cookie in the login route response (most likely solution)
- Use `cookies()` from `next/headers` to read token in server components
- Write middleware.ts to protect routes by checking cookie existence

---

## Current State of Files

| File                             | Status         | Notes                                           |
| --------------------------------- | -------------- | ----------------------------------------------- |
| `app/api/auth/register/route.ts` | PASS: Complete    | Works, tested                                   |
| `app/api/auth/login/route.ts`    |  In Progress | Token generates but not setting cookie yet      |
| `lib/auth.ts`                    | PASS: Complete    | JWT helpers, all tested                         |
| `middleware.ts`                  |  Not Started | Route protection, needs cookie read logic first |
| `app/login/page.tsx`             |  Not Started | UI not started                                  |

---

## Decisions Made

- **httpOnly cookie over localStorage** — reason: prevents XSS token theft, works with SSR
- **Custom auth over Next-Auth** — reason: Next-Auth conflicts with our Prisma setup, not worth the fight

---

## Blockers & Open Questions

- Does `cookies().set()` work inside a Route Handler or only in Server Actions? Need to verify.

---

## Exact Next Step

In `app/api/auth/login/route.ts`, after generating the JWT, set it as an httpOnly
cookie using `cookies().set('token', jwt, { httpOnly: true, secure: true, sameSite: 'strict' })`.
Then test with Postman — the response should include a `Set-Cookie` header.
```

---

## Notes

- This is a general-purpose, cross-project scratch/handoff file — separate from and not a
  substitute for a zeno-governed repo's `.zeno/project.md` (State/Next step/Proof, git-committed).
  Use `.zeno/` for durable per-repo backlog state; use `/save-session` for ephemeral,
  uncommitted context handoff — especially outside zeno-governed repos, or mid-task before hitting
  context limits.
- Each session gets its own file — never append to a previous one
- "What Did NOT Work" is the section that matters most — without it, future sessions will blindly retry approaches that already failed
- If asked to save mid-session rather than at the end, save what's known so far and mark in-progress items clearly as in-progress
- This file is what `/resume-session` reads to brief the next session
- Canonical store: `~/.claude/session-data/`
- Prefer the short-id filename form (`YYYY-MM-DD-<short-id>-session.tmp`) for any new file
