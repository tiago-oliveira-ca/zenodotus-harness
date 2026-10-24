---
name: developer-handoff-standards
description: >
  Standards for the designer-to-developer handoff process. Use when packaging design work
  for engineering implementation — organizing design files, defining design tokens, documenting
  component states and interactions, preparing assets, and writing accessibility notes.
  Trigger on: "prepare for handoff", "design handoff", "what do developers need from design",
  "design tokens", "ready for dev", "Figma annotations", "document this design", "export
  assets", "design QA", or any task bridging design to engineering implementation.
---

# Developer Handoff Standards

Use this skill when packaging design work for implementation. A good handoff gives delivery
teams a clear source of truth, not just polished mockups.

**Design-token arbitration** (CLAUDE.md lane row): token *architecture* (tiers, DTCG, naming systems) is owned by `zeno-stack/zeno-design-system`; visual *direction* by `zeno-stack/zeno-frontend-design`; this skill owns only the handoff *packaging* — how tokens and specs are communicated to developers.

## Core Boundaries

- **Design system** defines reusable standards and tokens.
- **Developer handoff** packages the specific assets, states, rules, and links needed for
  implementation.
- **Functional specs** explain behavior in prose when the design alone is insufficient.

## Required Artifacts

A complete handoff should include:

- organized source design files
- responsive guidance or breakpoint-specific mocks
- design tokens for typography, color, spacing, and motion
- exported assets in implementation-friendly formats
- interaction states, form feedback, loading, empty, and error states
- accessibility notes for semantics, focus, contrast, labels, and alt text
- references to tickets, stories, or implementation scope

## Workflow

1. Involve engineers before designs are frozen.
2. Run a pre-handoff review for feasibility and component reuse.
3. Deliver final mocks with tokens, assets, and edge-case states.
4. Walk through the design with implementers.
5. Support implementation asynchronously and perform design QA before release.

## Design Token Naming Conventions

Use a consistent naming structure so tokens map directly to code variables without translation:

```
[category]-[variant]-[state]
```

| Category | Token Examples | CSS Variable |
|---|---|---|
| **Color** | `color-primary-500`, `color-error-default` | `--color-primary-500` |
| **Typography** | `font-size-lg`, `font-weight-bold`, `font-family-mono` | `--font-size-lg` |
| **Spacing** | `space-4`, `space-8`, `space-16` | `--space-4` |
| **Radius** | `radius-sm`, `radius-full` | `--radius-sm` |
| **Shadow** | `shadow-card`, `shadow-overlay` | `--shadow-card` |
| **Motion** | `duration-fast`, `easing-spring` | `--duration-fast` |
| **Z-index** | `z-modal`, `z-toast`, `z-dropdown` | `--z-modal` |

**Rules:**
- Token names in Figma and code must be **identical**.
- Use semantic names for intent (`color-error`) not value (`color-red-500`).
- Reference base tokens in component tokens (`color-button-bg: var(--color-primary-500)`).
- Export tokens as JSON (Design Tokens Community Group format) for automated import.

## Component State Documentation

Every interactive component in the handoff must include mocks for:

| State | Required? | Notes |
|---|---|---|
| Default / resting | Yes | |
| Hover | Yes | |
| Focus (keyboard) | Yes | Must show visible focus ring |
| Active / pressed | Yes | |
| Disabled | Yes | |
| Loading | When async action | Show spinner or skeleton |
| Empty | When list/content | Empty state illustration or message |
| Error | When validation | Inline error label, color, icon |
| Success | When confirmation | |

## Communication Rules

- Use the same component and token names in design tools and code.
- Leave notes in-context where ambiguity would otherwise create rework.
- Make update notifications explicit when assets or specs change after handoff.

## Anti-pattern quick reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Mismatched naming between design tool and code | Every token requires manual translation and drifts silently over time | Use identical token names in Figma and code, per Design Token Naming Conventions |
| Missing interaction states | Engineers guess or skip hover/focus/error states, producing inconsistent implementation | Cover every required state in Component State Documentation before handoff |
| Frozen design with no engineer involvement | Feasibility issues are discovered after handoff, causing rework | Involve engineers before designs are frozen; run a pre-handoff feasibility review |
| Handoff treated as a one-time drop | Design and implementation silently diverge after handoff | Support implementation asynchronously; make update notifications explicit when specs change |
| Accessibility as an afterthought | Semantics, focus, and contrast gaps are discovered during QA or after release | Document accessibility notes as a required artifact, not a follow-up task |
| No design QA before release | Fidelity gap between final design and shipped UI goes unnoticed | Perform design QA before release, per the Workflow |

## Pre-flight checklist — run before delivering any design handoff

- [ ] Final source files are organized and implementation-ready
- [ ] Tokens and assets are linked or exported clearly
- [ ] Interactive, validation, loading, and error states are covered
- [ ] Mobile and desktop behavior are both addressed
- [ ] Accessibility expectations are explicit
- [ ] Engineers know where to ask follow-up questions
