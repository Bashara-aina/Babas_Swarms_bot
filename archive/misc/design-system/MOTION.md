# Motion System — MOTION.md

> **Version:** 1.0.0 | **Last updated:** 2026-04-16

---

## Table of Contents

1. [Core Principles](#1-core-principles)
2. [Duration Tokens](#2-duration-tokens)
3. [Easing Tokens](#3-easing-tokens)
4. [Spring Easing](#4-spring-easing)
5. [Scroll Reveal Pattern](#5-scroll-reveal-pattern)
6. [Micro-interactions](#6-micro-interactions)
7. [Page Transitions](#7-page-transitions)
8. [Component Library Selection](#8-component-library-selection)
9. [Aceternity/Magic UI — Use Selectively](#9-aceternitymagic-ui--use-selectively)
10. [Reduced Motion](#10-reduced-motion)
11. [Motion Checklist](#11-motion-checklist)

---

## 1. Core Principles

| Rule | Value |
|---|---|
| Micro-interactions | **150–300ms** |
| Complex transitions | **≤400ms** |
| Easing — entering | **ease-out** |
| Easing — exiting | **ease-in** |
| Animated properties | `transform`, `opacity`, `clip-path` ONLY |
| Never animate | `width`, `height`, `top`, `left`, `margin`, `padding` |
| Max animated elements per viewport | **1–2** |

**Why these constraints?** Animating layout-triggering properties (`width`, `height`) forces the browser to recalculate layout on every frame — causing jank. `transform` and `opacity` are GPU-accelerated and composited on the compositor thread, making 60fps guaranteed.

```css
/* ✅ CORRECT — GPU-composited */
transform: translateY(8px);
opacity: 0;

/* ❌ WRONG — triggers layout recalculation */
width: 100%;
height: auto;
```

---

## 2. Duration Tokens

```css
:root {
  /* Micro — button hovers, toggles, tooltips */
  --duration-micro:   100ms;

  /* Fast — small UI feedback, focus rings */
  --duration-fast:    150ms;

  /* Normal — default for most UI transitions */
  --duration-normal:  200ms;

  /* Slow — page transitions, drawers, modals */
  --duration-slow:    300ms;

  /* Complex — multi-step animations, skeleton shimmer */
  --duration-complex: 400ms;
}
```

**Pairing guide:**
| Interaction | Duration | Easing |
|---|---|---|
| Button hover | `--duration-micro` | `--ease-spring` |
| Focus ring appear | `--duration-fast` | `--ease-out` |
| Tooltip appear | `--duration-fast` | `--ease-spring` |
| Modal / drawer open | `--duration-slow` | `--ease-spring` |
| Page fade | `--duration-normal` | `--ease-enter` |
| Skeleton shimmer | `--duration-complex` | linear (loop) |

---

## 3. Easing Tokens

```css
:root {
  /* PRIMARY — spring-like, for entrances and interactive feedback */
  --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);

  /* Standard — safe fallback for all transitions */
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);

  /* Entrance — slow start, decelerate to rest */
  --ease-enter: cubic-bezier(0.0, 0, 0.2, 1);

  /* Exit — fast start, accelerate out */
  --ease-exit: cubic-bezier(0.4, 0, 1, 1);

  /* Linear — reserved for continuous animations (shimmer, spin) */
  --ease-linear: linear;
}
```

**Mental model:** Objects entering the screen need to decelerate (ease-out). Objects leaving need to accelerate (ease-in). Interactive feedback (button press, toggle) needs a bounce — that's the spring curve.

### Easing Visual Reference

```
ease-spring:  ████████████░░░░░░░░  (fast start, long deceleration)
ease-enter:  ██████████████░░░░░░░  (decelerate from start)
ease-exit:  ░░░░░░░████████████  (accelerate to end)
ease-default: ██████████░░░░░░░░░  (gentle in and out)
```

---

## 4. Spring Easing

The spring easing curve `--ease-spring: cubic-bezier(0.16, 1, 0.3, 1)` is the single most impactful motion token. It makes UI feel **alive** rather than mechanical.

**How to use it:**
```css
.button {
  transition: transform var(--duration-fast) var(--ease-spring),
              background-color var(--duration-fast) var(--ease-default);
}

.button:hover {
  transform: translateY(-2px); /* subtle lift on hover */
}

.button:active {
  transform: translateY(0px) scale(0.98); /* press down on click */
}
```

**Why `0.16, 1, 0.3, 1`?**
This is the **"expo out"** curve. It starts fast (0.16) and decelerates smoothly (1, 0.3, 1 controls the deceleration). It feels snappy without being abrupt. For comparison: `ease-out` alone doesn't decelerate as gracefully; this spring curve has a longer, more satisfying tail.

---

## 5. Scroll Reveal Pattern

```css
/* Base reveal animation */
@keyframes reveal {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Apply with stagger via animation-delay */
.reveal {
  animation: reveal 400ms var(--ease-spring) both;
}

/* Stagger children */
.reveal-group > *:nth-child(1) { animation-delay: 0ms; }
.reveal-group > *:nth-child(2) { animation-delay: 80ms; }
.reveal-group > *:nth-child(3) { animation-delay: 160ms; }
.reveal-group > *:nth-child(4) { animation-delay: 240ms; }
.reveal-group > *:nth-child(5) { animation-delay: 320ms; }
```

**Intersection Observer trigger:**
```typescript
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('reveal');
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
);

document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
```

**Exit animation (60–70% of enter):**
```css
.reveal-exit {
  animation: reveal-out 260ms var(--ease-exit) both;
}

@keyframes reveal-out {
  from { opacity: 1; transform: translateY(0); }
  to   { opacity: 0; transform: translateY(-8px); }
}
```

---

## 6. Micro-interactions

### Button Press
```css
.btn {
  transition: transform var(--duration-micro) var(--ease-spring),
              box-shadow var(--duration-micro) var(--ease-default);
}
.btn:hover  { transform: translateY(-1px); }
.btn:active { transform: translateY(0px) scale(0.97); }
```

### Toggle Switch
```css
.toggle-track {
  transition: background-color var(--duration-normal) var(--ease-default);
}
.toggle-thumb {
  transition: transform var(--duration-normal) var(--ease-spring);
}
.toggle-input:checked + .toggle-track .toggle-thumb {
  transform: translateX(20px);
}
```

### Hover Card Lift
```css
.card {
  transition: transform var(--duration-fast) var(--ease-spring),
              box-shadow var(--duration-fast) var(--ease-default);
}
.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}
```

### Input Focus Ring
```css
.input {
  transition: border-color var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out);
}
.input:focus-visible {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px oklch(from var(--color-primary) l c h / 0.2);
}
```

### Skeleton Shimmer
```css
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-skeleton) 25%,
    var(--color-skeleton-shine) 50%,
    var(--color-skeleton) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s var(--ease-linear) infinite;
}
```

---

## 7. Page Transitions

### Fade + Slide (default)
```css
@keyframes page-enter {
  from {
    opacity: 0;
    transform: translateX(12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes page-exit {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(-12px);
  }
}

.page-enter {
  animation: page-enter 250ms var(--ease-out) both;
}
.page-exit {
  animation: page-exit 180ms var(--ease-in) both; /* 70% of enter */
}
```

### Modal / Dialog
```css
@keyframes modal-backdrop-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes modal-content-in {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-backdrop {
  animation: modal-backdrop-in var(--duration-normal) var(--ease-out) both;
}
.modal-content {
  animation: modal-content-in var(--duration-slow) var(--ease-spring) both;
}
```

### Drawer (vaul-style)
```css
.drawer {
  transition: transform var(--duration-slow) var(--ease-spring);
}
.drawer[data-state="closed"] {
  transform: translateX(100%);
}
.drawer[data-state="open"] {
  transform: translateX(0);
}
```

---

## 8. Component Library Selection

Use this decision tree for animation infrastructure:

| Use Case | Library | Why |
|---|---|---|
| Hover, button press, toggle, tooltip | **tailwindcss-motion** | Tailwind-native, zero extra JS, performant |
| Page transitions, layout animations, drag | **Motion (Framer Motion v11+)** | Spring physics, layout animations, gestures |
| Scroll-triggered reveals, parallax, timelines | **GSAP + ScrollTrigger** | Most powerful scroll engine, timeline-based |
| Hero sections, dramatic entry moments | **Magic UI** ( Aceternity) | Beautiful components, use sparingly |
| Mobile drawers, bottom sheets | **vaul** | Emil Kowalski's drawer, spring physics, accessible |
| Toast notifications, popovers | **sonner** | Emil Kowalski's toast, great DX, accessible |
| Command palette animation | **cmdk** | Built-in animation, accessible ⌘K |

### Tailwind + Motion Setup
```bash
npm install tailwindcss-motion
```

```typescript
// tailwind.config.ts
import tailwindcssMotion from "tailwindcss-motion";

export default {
  plugins: [tailwindcssMotion()],
};
```

```tsx
// Usage
<div className="motion-safe:motion-opacity-0 motion-translate-y-4 motion:hover:motion-opacity-100 motion:hover:motion-translate-y-0 transition-spring duration-200">
  Hover me
</div>
```

---

## 9. Aceternity/Magic UI — Use Selectively

Magic UI / Aceternity components are **production-quality** but should be used as **spices, not the whole meal.** One per page maximum.

### ✅ Use These (they ship at Linear/Vercel quality)
| Component | When to use |
|---|---|
| **Dock** | macOS-style navigation dock — great for toolbars |
| **Spotlight** | Subtle radial glow following cursor — hero backgrounds |
| **Bento Grid** | Dashboard layouts with asymmetric card grids |
| **Animated Gradient Text** | Hero headline only (1 per page, no more) |

### ❌ Never Use These
- Particle systems / Confetti
- Shooting stars / comet effects
- 3D card flips
- Glowing orbs or blob animations
- More than 2 Magic UI components on a single viewport
- Any animation that auto-plays and can't be disabled

---

## 10. Reduced Motion

**Always wrap animations in `prefers-reduced-motion`.** For users with vestibular disorders, motion can cause nausea and dizziness.

```css
@media (prefers-reduced-motion: reduce) {
  :root {
    /* Kill all spring — instant transitions */
    --ease-spring:  var(--ease-default);
    --ease-enter:   var(--ease-default);
    --ease-exit:    var(--ease-default);

    /* Zero out durations */
    --duration-micro:   0ms;
    --duration-fast:     0ms;
    --duration-normal:   0ms;
    --duration-slow:     0ms;
    --duration-complex:  0ms;
  }

  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Functional reduced-motion intent

The `prefers-reduced-motion` media query has two modes:
1. **No motion preferred** — user is sensitive to motion → eliminate all transforms/translations
2. **No preference** — animate freely

```css
/* Fallback for browsers that don't support prefers-reduced-motion */
@media (prefers-reduced-motion: no-preference) {
  .reveal {
    animation: reveal 400ms var(--ease-spring) both;
  }
}
```

---

## 11. Motion Checklist

Before shipping any UI with animation, run through this:

- [ ] **CSS variables** — All durations and easings use `--duration-*` and `--ease-*` tokens, never hardcoded values
- [ ] **Reduced motion** — `prefers-reduced-motion: reduce` kills all motion; layout is unaffected
- [ ] **Exit duration** — 60–70% of enter duration (feels snappy, not sluggish)
- [ ] **GPU-only properties** — `transform` and `opacity` only; no `width`/`height`/`top`/`left`
- [ ] **No layout-triggering** — `box-shadow` is OK, `width` is not
- [ ] **Max 1–2 animated elements** per viewport — not everything animates
- [ ] **Spring easing** — `--ease-spring` on interactive elements (hover, press, toggle)
- [ ] **Linear** — reserved for continuous loops (skeleton shimmer, spinner)
- [ ] **Interruptible** — animations can be interrupted mid-way (e.g., mouse leaves hover mid-transition)
- [ ] **No autoplay** — animations triggered by user action or Intersection Observer, not page load

---

*Last reviewed: 2026-04-16 | Curve source: expo-out (0.16, 1, 0.3, 1) — Linear+ partners design system reference*
