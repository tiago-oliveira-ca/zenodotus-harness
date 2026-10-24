---
description: Load the most recent session file from ~/.claude/session-data/ and resume work with full context from where the last session ended.
---

# /resume-session

> **Contract owner:** the `zeno-stack/zeno-sessions` skill defines this lane's shared contract — filename convention, section format, alias store, and the prefer-`.zeno/`-when-tracked rule. The three session commands implement that contract; on a conflict, the skill wins.

Loads a saved session file and requires full absorption of it before any work resumes. Pairs with
`/save-session`, which writes the file this command reads back.

**Related:** if the current repo has `.zeno/project.md`, prefer `/zeno resume` for that repo's
tracked backlog — `/resume-session` is the separate, ad hoc scratch-file mechanism for cross-project
or non-zeno-governed handoff.

## When to use it

- Picking work back up on a new day
- Recovering after a fresh session was forced by hitting context limits
- Taking over a session file someone else produced (pass its path directly)
- Any time a session file exists and the goal is to get Claude fully oriented before proceeding

## Invocation forms

```
/resume-session                                                      # most recently modified file in ~/.claude/session-data/
/resume-session 2024-01-15                                           # most recent session for that date
/resume-session ~/.claude/session-data/2024-01-15-abc123de-session.tmp  # a specific current-format (short-id) file
/resume-session ~/.claude/sessions/2024-01-15-session.tmp               # a specific legacy-format file
```

## Process

### Step 1 — Locate the file

With no argument:

1. List `~/.claude/session-data/`.
2. Select the most recently modified `*-session.tmp` file.
3. If the directory is missing or nothing matches, say so and stop:
   ```
   No session files found in ~/.claude/session-data/
   Run /save-session at the end of a session to create one.
   ```

With an argument:

- A `YYYY-MM-DD`-shaped argument is a date: search `~/.claude/session-data/` first, then the
  legacy `~/.claude/sessions/`, for either `YYYY-MM-DD-session.tmp` (legacy) or
  `YYYY-MM-DD-<shortid>-session.tmp` (current), and take whichever match for that date is newest.
- Anything that looks like a path is read directly.
- Nothing found → report clearly and stop.

### Step 2 — Read it in full

Read the whole file before producing any summary.

### Step 3 — Brief back what was found

Reply using this exact structure, all sections present even when a section is empty:

```
SESSION LOADED: [actual resolved path to the file]
════════════════════════════════════════════════

PROJECT: [project name / topic from file]

WHAT WE'RE BUILDING:
[2-3 sentence summary in your own words]

CURRENT STATE:
PASS: Working: [count] items confirmed
 In Progress: [list files that are in progress]
 Not Started: [list planned but untouched]

WHAT NOT TO RETRY:
[list every failed approach with its reason — this is critical]

OPEN QUESTIONS / BLOCKERS:
[list any blockers or unanswered questions]

NEXT STEP:
[exact next step if defined in the file]
[if not defined: "No next step defined — recommend reviewing 'What Has NOT Been Tried Yet' together before starting"]

════════════════════════════════════════════════
Ready to continue. What would you like to do?
```

### Step 4 — Hold for the user

No automatic work, no file edits, until the user responds.

If the file defines a clear next step and the user confirms with something like "continue" or
"yes," carry out exactly that step. If no next step is defined, ask where to start — the "What
Has NOT Been Tried Yet" section is a reasonable prompt for suggestions.

---

## Edge cases

**Two sessions share a date** (`2024-01-15-session.tmp` and `2024-01-15-abc123de-session.tmp`):
take whichever was modified more recently, regardless of legacy vs. current naming.

**A referenced file no longer exists on disk:** flag it in the briefing —
"WARNING: `path/to/file.ts` referenced in session but not found on disk."

**The session is more than 7 days old:** flag the age —
"WARNING: This session is from N days ago (threshold: 7 days). Things may have changed." — then
continue normally.

**A file path is handed over directly** (e.g. forwarded by a teammate): read it and produce the
same briefing — the format doesn't change based on where the file came from.

**The file is empty or unreadable:** report "Session file found but appears empty or unreadable.
You may need to create a new one with /save-session."

---

## Worked example

```
SESSION LOADED: /Users/you/.claude/session-data/2024-01-15-abc123de-session.tmp
════════════════════════════════════════════════

PROJECT: my-app — JWT Authentication

WHAT WE'RE BUILDING:
User authentication with JWT tokens stored in httpOnly cookies.
Register and login endpoints are partially done. Route protection
via middleware hasn't been started yet.

CURRENT STATE:
PASS: Working: 3 items (register endpoint, JWT generation, password hashing)
 In Progress: app/api/auth/login/route.ts (token works, cookie not set yet)
 Not Started: middleware.ts, app/login/page.tsx

WHAT NOT TO RETRY:
FAIL: Next-Auth — conflicts with custom Prisma adapter, threw adapter error on every request
FAIL: localStorage for JWT — causes SSR hydration mismatch, incompatible with Next.js

OPEN QUESTIONS / BLOCKERS:
- Does cookies().set() work inside a Route Handler or only Server Actions?

NEXT STEP:
In app/api/auth/login/route.ts — set the JWT as an httpOnly cookie using
cookies().set('token', jwt, { httpOnly: true, secure: true, sameSite: 'strict' })
then test with Postman for a Set-Cookie header in the response.

════════════════════════════════════════════════
Ready to continue. What would you like to do?
```

---

## Notes

- The session file is a read-only historical record — never modify it while loading.
- Every section of the briefing format is fixed and must appear, even when empty.
- "What Not To Retry" is always shown, even as "None" — too easy to lose otherwise.
- After resuming, running `/save-session` again at the end of the new session produces a fresh
  dated file for next time.
