---
name: zeno-browser-qa
description: >
  Live browser QA using browser-automation MCP tools (claude-in-chrome, Playwright,
  Puppeteer) — smoke test, interaction test, visual regression, and accessibility passes
  against a running app, with a mandatory read-only-by-default safety posture. Use after
  deploying to staging/preview, before shipping a frontend change, or when reviewing a PR that
  touches UI. Trigger on: "QA this page", "check the deployed site", "verify the UI works",
  "smoke test the app", "visual regression check", "browser QA", "test this on staging",
  "does the page work", "check Core Web Vitals", "post-deploy check".
---

# Zeno Browser QA

Drives a live page like a real user through a browser-automation MCP, rather than a scripted
test suite — for verifying that a deployed build actually works, not just that its unit tests
pass. Pair with `zeno-e2e-testing` for the scripted, repeatable version of the same checks.

## When to run this

- After a deploy to staging or preview, before promoting further
- Before shipping — confirm layouts, forms, and interactions actually work end to end
- Reviewing a PR that touches frontend code
- Accessibility or responsive spot-checks outside a full audit

## Safety posture — read-only by default

Browser QA drives real auth and real user journeys against a real environment, so blast radius
is not optional to think about:

- **Never run a mutating journey** (checkout, payment, delete, mass-update) against a
  **production** URL. Mutating journeys require an explicit opt-in from the user *and* a
  staging/preview URL — both, not either.
- **Use seeded test credentials**, never real production logins.
- **Redact** credentials, tokens, and PII before saving or sharing any screenshot.
- Default every run to read-only: navigate, observe, assert on visible state. Treat anything
  that changes data as requiring explicit permission first.

## Phase 1 — smoke test

1. Navigate to the target URL.
2. Check the console for errors, filtering out known noise (analytics, third-party widgets).
3. Confirm no 4xx/5xx responses in the network log.
4. Screenshot above-the-fold at desktop and mobile viewports.
5. Check Core Web Vitals: LCP < 2.5s, CLS < 0.1, INP < 200ms (INP replaced FID as the
   responsiveness metric in March 2024 — use it, not FID, per web.dev's current thresholds).

## Phase 2 — interaction test

1. Click every nav link — verify none are dead.
2. Submit forms with valid data — verify the success state.
3. Submit forms with invalid data — verify the error state renders, not just that submission
   is blocked.
4. Exercise the auth flow (login → protected page → logout) with test credentials only.
5. Walk critical user journeys (checkout, onboarding, search) **read-only by default** —
   only exercise a mutating journey against staging, and only with explicit opt-in (see
   Safety posture above).

## Phase 3 — visual regression

1. Screenshot key pages at three breakpoints: 375px, 768px, 1440px.
2. Compare against committed baseline screenshots.
3. **No baseline means the check is inconclusive — report it as such, never as a silent
   pass.** A visual check with nothing to compare against has proven nothing.
4. Flag layout shifts greater than 5px, missing elements, or overflow.
5. Check dark mode if the app supports it.

## Phase 4 — accessibility

1. Run axe-core (or equivalent) on each page.
2. Flag WCAG 2.2 AA violations: contrast, missing labels, focus order.
3. Verify keyboard navigation works end to end — tab order, visible focus, no traps.
4. Check screen-reader landmarks (main, nav, headings in order).

axe-core covers roughly 30-40% of WCAG automatically. A clean automated run is **necessary,
not sufficient** — it does not license reporting a page as "accessible." Keyboard navigation,
focus order, and a screen-reader pass still require a manual check. See `zeno-accessibility`
for the full standard this phase is sampling from.

## Reporting

Always end with a report in this shape, and always state a verdict:

```markdown
## QA Report — [URL] — [timestamp]

### Smoke Test
- Console errors: 0 critical, 2 warnings (analytics noise)
- Network: all 200/304, no failures
- Core Web Vitals: LCP 1.2s / CLS 0.02 / INP 89ms — all within budget

### Interactions
- [x] Nav links: 12/12 working
- [ ] Contact form: missing error state for invalid email
- [x] Auth flow: login/logout working

### Visual
- [ ] Hero section overflows at 375px
- [x] Dark mode: consistent across pages checked

### Accessibility
- 2 AA violations: missing alt text on hero image, low-contrast footer links

### Verdict: SHIP WITH FIXES (2 issues, 0 blockers)
```

Verdict is one of `SHIP`, `SHIP WITH FIXES`, `DO NOT SHIP`, or `INCONCLUSIVE` (use
`INCONCLUSIVE` whenever a phase couldn't run — e.g. no visual baseline — rather than omitting
that phase silently).

## Tooling

Use whichever browser-automation MCP is available in the session — `claude-in-chrome` for
interactive inspection against your actual signed-in Chrome, a Playwright MCP or direct
Playwright script for scripted, repeatable runs. Prefer `claude-in-chrome` for one-off
exploratory QA; prefer Playwright when the same check needs to run again later (in which case
consider promoting it into the `zeno-e2e-testing` suite instead of re-running it by hand).

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Running a mutating journey against production | Require staging URL + explicit opt-in for any mutating journey |
| Real production credentials in a QA run | Seeded test credentials only |
| Unredacted screenshot with tokens/PII visible | Redact before saving or sharing |
| Reporting "no visual regressions" with no baseline | Report `INCONCLUSIVE` — nothing was actually compared |
| "Passed axe-core" reported as "accessible" | Axe covers ~30-40% of WCAG; still needs a manual keyboard/screen-reader pass |
| Skipping the verdict line | Every report ends with one of SHIP / SHIP WITH FIXES / DO NOT SHIP / INCONCLUSIVE |

## Pre-flight checklist — run before delivering any browser QA report

- [ ] Target URL confirmed as staging/preview before any mutating action is even considered
- [ ] Test credentials used, never production logins
- [ ] Screenshots redacted of any credentials, tokens, or PII
- [ ] All four phases attempted (smoke, interaction, visual, accessibility) or their omission explained
- [ ] Visual regression has a real baseline, or is explicitly marked `INCONCLUSIVE`
- [ ] Accessibility findings are scoped to what was actually checked, not overclaimed
- [ ] Report includes a single, explicit verdict
