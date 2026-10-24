---
name: zeno-motion-ui
description: >
  Production motion system for React/Next.js using the `motion` (formerly Framer Motion)
  library — motion tokens, AnimatePresence modes, performance rules, device adaptation,
  reduced-motion support, and modal/list/scroll patterns. Use when implementing animations,
  transitions, or any motion pattern. Trigger on: "add an animation", "animate this
  component", "AnimatePresence", "modal transition", "reduced motion", "motion tokens",
  "stagger a list", "scroll parallax", "why is this animation janky".
---

# Motion UI

A motion system for React/Next.js built on performance and accessibility, not decoration.
Every animation should earn its place by guiding attention, communicating state, or preserving
spatial continuity across a layout change — if it does none of those, remove it.

## When motion belongs, and when it doesn't

Appropriate: interactive components (buttons, modals, menus), state transitions (loading ->
loaded, open -> closed), and navigation/layout continuity (shared elements, crossfades).

Skip it when: it's purely decorative, it reduces usability or clarity, or it costs more
performance than the payoff justifies. Prioritize responsiveness over visual smoothness, adapt
for low-end devices, and always support reduced motion.

## Package and version

```bash
npm install motion
```

`motion/react` is the current package for Motion-for-React projects; `framer-motion` is the
legacy import path for projects still on the old package. **Never mix them in one project** —
they run separate internal schedulers, and `AnimatePresence` from one package will not
coordinate exit animations with components from the other. Check which the project uses before
writing any animation code:

```bash
cat package.json | grep -E '"motion"|"framer-motion"'
```

```ts
// Correct (modern)
import { motion, AnimatePresence } from "motion/react"
// Correct (legacy)
import { motion, AnimatePresence } from "framer-motion"
// Never both in the same project
```

## Motion tokens

Centralize duration, easing, and distance so animations stay consistent across the app instead
of each component inventing its own numbers:

```ts
// motionTokens.ts
export const motionTokens = {
  duration: { fast: 0.18, normal: 0.35, slow: 0.6 },
  // Use as the `ease` value inside a transition object:
  // transition={{ duration: motionTokens.duration.normal, ease: motionTokens.easing.smooth }}
  easing: {
    smooth: [0.22, 1, 0.36, 1] as [number, number, number, number],
    sharp:  [0.4,  0, 0.2, 1] as [number, number, number, number],
  },
  distance: { sm: 8, md: 16, lg: 24 },
}
```

```tsx
import { motionTokens } from "@/lib/motionTokens"

<motion.div
  initial={{ opacity: 0, y: motionTokens.distance.md }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: motionTokens.duration.normal, ease: motionTokens.easing.smooth }}
/>
```

## Performance rules

Animate `transform` and `opacity` — both are compositor-only and cheap. Avoid animating
`width`/`height`/`top`/`left` — they trigger layout on every frame. When in doubt, responsiveness
beats smoothness.

## Device adaptation

Combine CPU core count and available memory for a more reliable "low-end" signal than either
alone — `deviceMemory` is Chrome/Android-only, so the core-count fallback covers Safari/Firefox:

```ts
const isLowEnd =
  typeof navigator !== "undefined" && (
    (navigator.deviceMemory !== undefined && navigator.deviceMemory <= 2) ||
    (navigator.deviceMemory === undefined && navigator.hardwareConcurrency <= 4)
  )

const duration = isLowEnd ? 0.2 : 0.4
```

## Accessibility

Respect `prefers-reduced-motion` at both the JS and CSS layer — see `zeno-accessibility` for
the broader reduced-motion discipline this feeds into.

```tsx
import { motion, useReducedMotion } from "motion/react"

export function FadeIn() {
  const reduce = useReducedMotion()
  return <motion.div initial={{ opacity: 0, y: reduce ? 0 : 24 }} animate={{ opacity: 1, y: 0 }} />
}
```

```css
@media (prefers-reduced-motion: reduce) {
  .motion-safe-transition { transition: opacity 0.2s; }
  .motion-reduce-transform { transform: none !important; }
}
```

```html
<div class="motion-safe:animate-fade motion-reduce:opacity-100"></div>
```

## Core patterns by scenario

| Scenario | Pattern |
|---|---|
| Hover feedback | `whileHover` |
| Tap / press feedback | `whileTap` |
| Reveal on scroll | `whileInView` |
| Scroll-linked value | `useScroll` + `useTransform` |
| Conditional mount/unmount | `AnimatePresence` |
| Small layout shift (single element, < ~300px change) | `layout` prop |
| Large layout shift or full-page reflow | Avoid `layout` — use CSS transitions or page-level routing |
| Complex, imperative sequences | `useAnimate` |

`layout` reconciles position via `transform`, but on elements spanning the viewport or
triggering deep reflow, the measurement cost itself causes visible jank and CLS. Prefer CSS
Grid/Flexbox transitions, or scope `layoutId` to specific child elements only.

Shared-element transitions use `layoutId` (must be unique per mounted instance — append a
per-item suffix like `` `shared-${item.id}` `` when multiple instances can exist at once).

## `AnimatePresence` modes

Always set `mode` explicitly. The default, `"sync"`, runs enter and exit simultaneously, which
visually overlaps in most UI patterns.

| `mode` | Use for |
|---|---|
| `"wait"` | Exit completes before enter starts — modals, toasts, page transitions |
| `"sync"` (default) | Enter and exit overlap — only when that's intentional, e.g. crossfade carousels |
| `"popLayout"` | Exiting element pops out of flow immediately, remaining items animate to fill — lists, tabs, dismissible cards |

```tsx
// Modal — always "wait"
<AnimatePresence mode="wait">{open && <Modal key="modal" />}</AnimatePresence>

// Dismissible list item — "popLayout"
<AnimatePresence mode="popLayout">
  {items.map(item => <Card key={item.id} />)}
</AnimatePresence>
```

## Modal essentials

A modal needs a focus trap, an Escape-to-close handler, a scroll lock, correct ARIA roles, and
`AnimatePresence mode="wait"` so the exit animation finishes before the next modal enters (see
`zeno-accessibility` for the full focus-management discipline this builds on):

```tsx
import React, { useEffect, useRef, useState } from "react"
import { motion, AnimatePresence } from "motion/react"

function useFocusTrap(ref: React.RefObject<HTMLDivElement | null>, active: boolean) {
  useEffect(() => {
    if (!active || !ref.current) return
    const el = ref.current
    const focusable = el.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    function handleKey(e: KeyboardEvent) {
      if (e.key !== "Tab") return
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus() }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus() }
    }
    el.addEventListener("keydown", handleKey)
    first?.focus()
    return () => el.removeEventListener("keydown", handleKey)
  }, [active, ref])
}

function useScrollLock(active: boolean) {
  useEffect(() => {
    if (!active) return
    const prev = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => { document.body.style.overflow = prev }
  }, [active])
}

function Modal({ open, closeModal }: { open: boolean; closeModal: () => void }) {
  const ref = useRef<HTMLDivElement>(null)
  useFocusTrap(ref, open)
  useScrollLock(open)

  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === "Escape") closeModal() }
    if (open) window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, closeModal])

  return (
    <AnimatePresence mode="wait">
      {open && (
        <motion.div role="dialog" aria-modal="true" aria-labelledby="modal-title"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }} className="fixed inset-0 flex items-center justify-center bg-black/40">
          <motion.div ref={ref} initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }} transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="bg-white p-6 rounded">
            <h2 id="modal-title">Dialog Title</h2>
            <button onClick={closeModal}>Close</button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
```

## SSR safety

Match initial state between server and client renders. Set `initial` explicitly rather than
relying on implicit animation origins. Wrap motion components in `"use client"` in the Next.js
App Router.

## Debugging checklist

Mixed imports (`motion/react` + `framer-motion`) in the same project; missing `"use client"`
in the App Router; a missing `key` on `AnimatePresence` children; a hydration mismatch (initial
state differs between SSR and client); `layout` misused on a large container causing reflow
jank; a state-driven animation that isn't firing (check the dependency array).

## QA checklist

No CLS, keyboard works, focus is trapped in modals, ARIA roles are correct
(`role="dialog"`, `aria-modal="true"`), reduced motion is respected (`useReducedMotion` + CSS
media query), no Next.js hydration warnings, animations stop cleanly on unmount, and `mode` is
set explicitly on every `AnimatePresence` usage.

## Additional examples

```tsx
// Button interaction
import { motion } from "motion/react"
export function Button() {
  return (
    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}
      transition={{ duration: 0.15, ease: [0.4, 0, 0.2, 1] }}>
      Click me
    </motion.button>
  )
}

// Stagger list — keep staggerChildren <= 0.1s or it reads as sluggish
const container = { hidden: {}, visible: { transition: { staggerChildren: 0.08 } } }
const item = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.22, 1, 0.36, 1] } },
}

// Scroll parallax
import { useScroll, useTransform, motion } from "motion/react"
export function Parallax() {
  const { scrollYProgress } = useScroll()
  const y = useTransform(scrollYProgress, [0, 1], [0, -80])
  return <motion.div style={{ y }} />
}

// Skeleton loading — duration matters; too short flashes instead of pulsing
<motion.div className="bg-gray-200 h-6 w-full rounded"
  animate={{ opacity: [0.5, 1, 0.5] }}
  transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }} />
```

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Animating `width`/`height`/`top`/`left` | Animate `transform`/`opacity` only |
| Mixing `motion/react` and `framer-motion` imports in one project | Pick one package and import consistently everywhere |
| Infinite animation with no state it communicates | Ask what state it signals; remove it if the answer is "nothing" |
| `staggerChildren` beyond ~0.1s | Keep it at or below 0.1s — longer reads as sluggish |
| Ignoring `prefers-reduced-motion` | `useReducedMotion()` in JS, matching `@media` rule in CSS |
| `layout` prop on a large or full-viewport container | CSS Grid/Flexbox transitions, or `layoutId` scoped to specific children |
| `AnimatePresence` with no explicit `mode` | Set `mode` explicitly — the `"sync"` default overlaps enter/exit visually |
| Motion used purely for decoration | Remove it — motion must guide attention, communicate state, or preserve spatial continuity |

## Pre-flight checklist — run before delivering any motion/animation change

- [ ] Only `transform`/`opacity` are animated, not layout-triggering properties
- [ ] Only one of `motion/react` or `framer-motion` is imported across the project
- [ ] `AnimatePresence` has an explicit `mode` at every usage site
- [ ] `useReducedMotion` (JS) and `prefers-reduced-motion` (CSS) are both respected
- [ ] Modals have a focus trap, Escape close, scroll lock, and correct ARIA roles
- [ ] `layoutId` values are unique per mounted instance
- [ ] The animation demonstrably guides attention, communicates state, or preserves spatial continuity — otherwise it's removed
