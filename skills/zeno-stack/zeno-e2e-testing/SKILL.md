---
name: zeno-e2e-testing
description: >
  Playwright end-to-end testing patterns: test file organization, the Page Object Model,
  Playwright configuration, flaky-test diagnosis and fixes, artifact management (screenshots,
  traces, video), and CI/CD wiring. Use when writing or reviewing browser-driven E2E suites,
  investigating a flaky test, or setting up Playwright in CI. Trigger on: "write an E2E test",
  "Playwright test", "page object model", "flaky test", "test is flaky", "E2E CI setup",
  "playwright.config", "screenshot on failure", "trace viewer", "retry a failing test",
  "end-to-end test suite".
---

# Zeno E2E Testing

Playwright patterns for E2E suites that stay fast, stable, and cheap to maintain. Complements
`zeno-react-testing` (component-level) — reach for this skill once behavior needs to be proven
through a real browser against a real (or staged) backend.

**Agent counterpart:** `agents/zeno-e2e-runner.md` runs this lane as a spawned pass on this same Playwright stack (optionally driven through Vercel Agent Browser where installed — a layer over Playwright, not a different stack).

## Suite layout

Group specs by domain, keep fixtures and page objects out of the spec tree, and give
Playwright its own config file at the project root:

```
tests/
├── e2e/
│   ├── auth/           login.spec.ts, logout.spec.ts, register.spec.ts
│   ├── features/       browse.spec.ts, search.spec.ts, create.spec.ts
│   └── api/            endpoints.spec.ts
├── fixtures/            auth.ts, data.ts
├── pages/                *Page.ts — one Page Object per screen
└── playwright.config.ts
```

## Page Object Model

Encapsulate locators and screen-level actions behind a class per page. Specs read as behavior,
not selector soup, and a selector change touches one file instead of every spec that uses it.

```typescript
import { Page, Locator } from '@playwright/test'

export class ItemsPage {
  readonly page: Page
  readonly searchInput: Locator
  readonly itemCards: Locator

  constructor(page: Page) {
    this.page = page
    this.searchInput = page.locator('[data-testid="search-input"]')
    this.itemCards = page.locator('[data-testid="item-card"]')
  }

  async goto() {
    await this.page.goto('/items')
    await this.page.waitForLoadState('networkidle')
  }

  async search(query: string) {
    await this.searchInput.fill(query)
    await this.page.waitForResponse(resp => resp.url().includes('/api/search'))
  }

  async getItemCount() {
    return this.itemCards.count()
  }
}
```

```typescript
import { test, expect } from '@playwright/test'
import { ItemsPage } from '../../pages/ItemsPage'

test.describe('Item Search', () => {
  let itemsPage: ItemsPage

  test.beforeEach(async ({ page }) => {
    itemsPage = new ItemsPage(page)
    await itemsPage.goto()
  })

  test('finds items by keyword', async ({ page }) => {
    await itemsPage.search('test')
    expect(await itemsPage.getItemCount()).toBeGreaterThan(0)
    await expect(itemsPage.itemCards.first()).toContainText(/test/i)
  })

  test('shows empty state for no matches', async ({ page }) => {
    await itemsPage.search('xyznonexistent123')
    await expect(page.locator('[data-testid="no-results"]')).toBeVisible()
  })
})
```

## Playwright configuration

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'playwright-results.xml' }],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
})
```

`forbidOnly` in CI catches an accidentally-committed `test.only`. `retries: 2` in CI absorbs
genuine environment jitter — it must never be the fix for a test that is actually flaky by
design; see below.

## Diagnosing and fixing flaky tests

First isolate whether a test is flaky at all, then find the real cause — never reach for
`retries` as the fix.

```bash
npx playwright test tests/search.spec.ts --repeat-each=10
```

Common causes, in order of frequency:

**Race condition — not waiting for the element's real ready state:**
```typescript
// Bad — assumes the click target is already interactable
await page.click('[data-testid="button"]')

// Good — Playwright's locator auto-waits for actionability
await page.locator('[data-testid="button"]').click()
```

**Network timing — waiting on a clock instead of an event:**
```typescript
// Bad — arbitrary timeout, races the actual response
await page.waitForTimeout(5000)

// Good — wait for the specific condition that matters
await page.waitForResponse(resp => resp.url().includes('/api/data'))
```

**Animation timing — interacting mid-transition:**
```typescript
await page.locator('[data-testid="menu-item"]').waitFor({ state: 'visible' })
await page.waitForLoadState('networkidle')
await page.locator('[data-testid="menu-item"]').click()
```

**Quarantine, don't silently skip**, while a fix is pending — always attach an issue link so
the test doesn't rot invisibly:

```typescript
test('complex search', async ({ page }) => {
  test.fixme(true, 'Flaky — see #123')
})

test('CI-only flake', async ({ page }) => {
  test.skip(process.env.CI, 'Flaky in CI — see #123')
})
```

## Critical and irreversible flows

For flows with real side effects (payments, destructive actions, anything hitting a live
external system), gate execution by environment and verify the flow through an intermediate
confirmation step rather than only the final state:

```typescript
test('checkout charges the card', async ({ page }) => {
  test.skip(process.env.NODE_ENV === 'production', 'Never exercise real payments in prod')

  await page.goto('/checkout')
  await page.locator('[data-testid="pay-now"]').click()
  await expect(page.locator('[data-testid="order-preview"]')).toContainText('$42.00')

  await page.locator('[data-testid="confirm-payment"]').click()
  await page.waitForResponse(
    resp => resp.url().includes('/api/checkout') && resp.status() === 200,
    { timeout: 30000 }
  )
  await expect(page.locator('[data-testid="order-success"]')).toBeVisible()
})
```

## Artifact management

Capture enough evidence to debug a CI failure without re-running it locally:

```typescript
// Full-page or scoped screenshot
await page.screenshot({ path: 'artifacts/after-login.png', fullPage: true })
await page.locator('[data-testid="chart"]').screenshot({ path: 'artifacts/chart.png' })
```

Configure `trace: 'on-first-retry'` and `video: 'retain-on-failure'` in `playwright.config.ts`
(above) rather than capturing unconditionally — always-on trace/video makes every run slower
and every artifact upload larger for no benefit on passing tests.

## CI/CD integration

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
        env:
          BASE_URL: ${{ vars.STAGING_URL }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

Run E2E against a staging URL, upload the HTML report `if: always()` (failures are exactly
when you need it), and keep retention short — these reports are for triage, not audit.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| `page.click()` on a raw selector | `page.locator(selector).click()` — auto-waits for actionability |
| `waitForTimeout(n)` to "let things settle" | `waitForResponse` / `waitForLoadState` on the actual condition |
| Bumping `retries` to make a flaky test pass | Diagnose the real cause (race, network, animation) first |
| Selectors duplicated across specs | One Page Object per screen; specs call its methods |
| Silently skipping a flaky test | `test.fixme`/`test.skip` with a linked issue, never a bare skip |
| Always-on video/trace capture | `on-first-retry` / `retain-on-failure` — capture only on signal |
| Exercising payment/destructive flows against prod | `test.skip` gated on `NODE_ENV`, confirm via an intermediate state first |

## Pre-flight checklist — run before delivering any E2E test suite

- [ ] Specs are grouped by domain; locators live in Page Objects, not inline in specs
- [ ] `playwright.config.ts` sets `forbidOnly` and `retries` conditioned on `CI`
- [ ] No `waitForTimeout` used as a substitute for a real wait condition
- [ ] Any flaky test found is diagnosed (race/network/animation), not just retried away
- [ ] Quarantined tests (`fixme`/`skip`) link to a tracking issue
- [ ] Critical/irreversible flows are gated by environment and skipped in production
- [ ] CI workflow installs browsers, runs the suite, and uploads the report on every outcome
