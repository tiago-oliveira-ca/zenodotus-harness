---
name: zeno-token-budget-advisor
description: >
  Offers an informed choice about response depth before answering, when the user explicitly wants
  to control response length/detail/token budget. Estimates input tokens and a response window by
  complexity, presents 25/50/75/100% depth options with the actual estimated numbers, then answers
  at the chosen level. Trigger on: "token budget", "token count", "token usage", "token limit",
  "response length", "answer depth", "short version", "brief answer", "detailed answer",
  "exhaustive answer", "respuesta corta vs larga", "dame la version corta". Do NOT trigger when a
  depth level was already set this session (maintain it silently), the answer is trivially one
  line, or "token" refers to an auth/session/payment token rather than response size.
---

# Zeno Token Budget Advisor — offer depth before answering

Intercepts the response flow to offer a choice about depth **before** answering, using an actual
estimated number rather than a vague "want the short version?"

## Step 1 — estimate input tokens

Use the same calibration heuristic as `zeno-stack/zeno-context-budget`:
- prose: `words × 1.3`
- code-heavy or mixed content: `chars / 4`
For genuinely mixed content, use the dominant content type and keep the estimate heuristic — this
isn't a real tokenizer, don't present it as one.

## Step 2 — estimate the response window by complexity

| Complexity | Multiplier range | Example prompts |
|---|---|---|
| Simple | 3x-8x | "What is X?", yes/no, single fact |
| Medium | 8x-20x | "How does X work?" |
| Medium-High | 10x-25x | Code request with context |
| Complex | 15x-40x | Multi-part analysis, comparisons, architecture |
| Creative | 10x-30x | Stories, essays, narrative writing |

Response window = `input_tokens x mult_min` to `input_tokens x mult_max`, capped at the model's
configured output-token limit.

## Step 3 — present the depth options

Present this before answering, with the actual estimated numbers filled in:

```
Analyzing your prompt...

Input: ~[N] tokens  |  Type: [type]  |  Complexity: [level]

Choose your depth level:

[1] Essential   (25%)  ->  ~[tokens]   Direct answer only, no preamble
[2] Moderate    (50%)  ->  ~[tokens]   Answer + context + 1 example
[3] Detailed    (75%)  ->  ~[tokens]   Full answer with alternatives
[4] Exhaustive (100%)  ->  ~[tokens]   Everything, no limits

Which level? (1-4, or say "25% depth" / "50% depth" / "75% depth" / "100% depth")

Precision: heuristic estimate, ~85-90% accuracy (+/-15%).
```

Per-level token target within the window: 25% = `min + (max-min)*0.25`, 50% = `min +
(max-min)*0.50`, 75% = `min + (max-min)*0.75`, 100% = `max`.

## Step 4 — answer at the chosen level

| Level | Target length | Include | Omit |
|---|---|---|---|
| 25% Essential | 2-4 sentences | Direct answer, key conclusion | Context, examples, nuance, alternatives |
| 50% Moderate | 1-3 paragraphs | Answer + necessary context + 1 example | Deep analysis, edge cases, references |
| 75% Detailed | Structured | Multiple examples, pros/cons, alternatives | Extreme edge cases, exhaustive references |
| 100% Exhaustive | No restriction | Everything — full analysis, all code, all perspectives | Nothing |

## Shortcuts — skip the question when the level is already stated

| What they say | Level |
|---|---|
| "1" / "25% depth" / "short version" / "brief answer" / "tldr" | 25% |
| "2" / "50% depth" / "moderate depth" / "balanced answer" | 50% |
| "3" / "75% depth" / "detailed answer" / "thorough answer" | 75% |
| "4" / "100% depth" / "exhaustive answer" / "full deep dive" | 100% |

If a level was set earlier in the session, **maintain it silently** for subsequent responses
unless the user changes it — don't re-ask every turn.

## Precision note

Heuristic estimation only, no real tokenizer. ~85-90% accuracy, +/-15% variance. Always show the
disclaimer line rather than presenting the numbers as exact.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Re-asking depth every turn after the user already chose | Maintain the chosen level silently for the rest of the session |
| Presenting the token estimate as exact | Always show the "+/-15%, heuristic" disclaimer |
| Triggering on "token" meaning an auth/payment token | Only trigger on response-length/depth intent |
| Triggering on a trivially one-line answer | Skip the prompt when the answer is obviously short |
| Guessing complexity without checking prompt content/code-density | Classify using the actual input (prose vs. code-heavy vs. mixed) |

## Pre-flight checklist — run before delivering any depth-gated response

- [ ] Input tokens were estimated using the prose/code-density heuristic, not guessed.
- [ ] The response window was computed from the correct complexity multiplier range.
- [ ] The depth-options block was shown with real numbers before answering (unless a level was already set, or a shortcut phrase matched).
- [ ] The precision disclaimer was included whenever an estimate was shown.
- [ ] The final response length actually matches the chosen level's target.
