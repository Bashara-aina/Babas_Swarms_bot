# UI/UX Excellence System — MASTER

> **Version:** 1.0.0 | **Last updated:** 2026-04-16
> **Design level:** Linear / Vercel / Stripe production quality

---

## Overview

This design system is a production-grade reference for building consistent, accessible, and polished user interfaces. It covers 4 interdependent subsystems:

| Subsystem | File | Purpose |
|---|---|---|
| **Tokens** | `TOKENS.md` | All primitive and semantic design values — color, type, space, shadow |
| **Components** | `COMPONENTS.md` | Component patterns — Card, Button, Form, Badge, Avatar, Skeleton, Toast |
| **Motion** | `MOTION.md` | Animation principles, timing, easing, and interaction choreography |
| **Layout** | `LAYOUT.md` | Grid, subgrid, container queries, spacing rhythm, forbidden patterns |

These 4 files are designed to be read together. Start with **TOKENS.md** to understand the primitive values, then build outward to components, motion, and layout.

---

## Quick Reference

### Design Token Core

```css
/* Color — OKLCH for perceptually uniform gradients */
--color-primary:     oklch(55% 0.18 250);   /* Hydra Teal accent */
--color-primary-hover: oklch(48% 0.20 250);
--color-surface:      oklch(98% 0 0);           /* Near-white surface */
--color-surface-offset: oklch(96% 0 0);
--color-text:        oklch(25% 0 0);           /* Near-black text */

/* Typography — fluid clamp() scale */
--text-xs:   clamp(0.694rem, 0.66rem + 0.17vw, 0.8rem);
--text-sm:   clamp(0.833rem, 0.78rem + 0.24vw, 1rem);
--text-base: clamp(1rem, 0.93rem + 0.29vw, 1.125rem);
--text-lg:   clamp(1.2rem, 1.1rem + 0.47vw, 1.5rem);
--text-xl:   clamp(1.44rem, 1.3rem + 0.65vw, 1.875rem);
--text-2xl:  clamp(1.728rem, 1.5rem + 1.06vw, 2.25rem);
--text-3xl:  clamp(2.074rem, 1.75rem + 1.51vw, 3rem);
--text-4xl:  clamp(2.488rem, 2rem + 2.26vw, 4rem);

/* Spacing — 4px base unit */
--space-1:  0.25rem;   /* 4px  */
--space-2:  0.5rem;    /* 8px  */
--space-3:  0.75rem;   /* 12px */
--space-4:  1rem;      /* 16px */
--space-6:  1.5rem;   /* 24px */
--space-8:  2rem;      /* 32px */
--space-12: 3rem;      /* 48px */
--space-16: 4rem;      /* 64px */
--space-24: 6rem;      /* 96px */

/* Easing */
--ease-spring:  cubic-bezier(0.16, 1, 0.3, 1);   /* Interactive feedback */
--ease-enter:   cubic-bezier(0.0, 0, 0.2, 1);      /* Elements entering */
--ease-exit:    cubic-bezier(0.4, 0, 1, 1);        /* Elements leaving */
--ease-default: cubic-bezier(0.4, 0, 0.2, 1);     /* Safe fallback */
--ease-linear: linear;                              /* Loops only */

/* Durations */
--duration-micro:   100ms;   /* Button hovers, toggles */
--duration-fast:    150ms;   /* Small UI feedback */
--duration-normal: 200ms;   /* Default transitions */
--duration-slow:    300ms;   /* Modals, drawers */
--duration-complex: 400ms;   /* Multi-step, shimmer */
```

### Component Quick Start

```tsx
// Card — surface elevation, hover lift
<Card variant="default" padding="md" className="hover:-translate-y-1 hover:shadow-md">
  {children}
</Card>

// Button — 44px min height, spring press
<Button variant="primary" size="md" loading={false}>
  Submit
</Button>

// Form Input — always has label, validates on blur
<Input label="Email address" type="email" error={emailError} required />

// Badge — status communication
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="error">Failed</Badge>

// Toast — sonner, classNames API
toast.success('Changes saved');
toast.error('Failed to save — check your connection');
```

### Motion Quick Start

```css
/* GPU-composited only — transform + opacity */
transition: transform var(--duration-fast) var(--ease-spring),
            opacity var(--duration-fast) var(--ease-default);

/* Spring easing — the single most impactful token */
--ease-spring: cubic-bezier(0.16, 1, 0.3, 1);

/* Exit = 60-70% of enter duration */
.page-enter  { animation: 250ms var(--ease-out) both; }
.page-exit  { animation: 180ms var(--ease-in) both; }   /* 180/250 = 72% ✓ */
```

### Layout Quick Start

```css
/* Auto-fit grid — replaces 3-column fixed */
.grid-auto-3 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
}

/* Container query — component responds to parent */
.card-wrapper {
  container-type: inline-size;
}
@container (min-width: 400px) {
  .card { grid-template-columns: 200px 1fr; }
}

/* Subgrid — card interiors align to outer grid */
.card {
  display: grid;
  grid-template-columns: subgrid;
}
```

---

## Design Principles

### 1. OKLCH for Color

All colors use the OKLCH color space, not HSL. OKLCH is perceptually uniform, which means gradient transitions look correct and color mixing produces expected results. The `oklch()` function also enables lightness-preserving hue rotation for dark mode.

```css
/* ❌ WRONG — HSL gradients show banding */
background: linear-gradient(hsl(200, 80%, 50%), hsl(260, 80%, 60%));

/* ✅ CORRECT — OKLCH gradients are smooth */
background: linear-gradient(oklch(55% 0.18 200), oklch(50% 0.20 260));
```

### 2. Semantic Tokens over Raw Values

Never use raw primitive values in component styles. Always reference semantic tokens. This allows theme changes to propagate correctly.

```css
/* ❌ WRONG — hardcoded primitive */
.card {
  background: oklch(98% 0 0);
  border: 1px solid oklch(from oklch(25% 0 0) l c h / 0.08);
}

/* ✅ CORRECT — semantic aliases */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}
```

### 3. GPU Compositing for Animation

Only animate `transform` and `opacity`. These are GPU-accelerated and composited on the compositor thread, making 60fps guaranteed. Animating `width`, `height`, `top`, or `left` forces the browser to recalculate layout on every frame.

```css
/* ❌ WRONG — layout-triggering */
width: 100%;
height: auto;

/* ✅ CORRECT — GPU-composited */
transform: translateY(8px);
opacity: 0;
```

### 4. Dark Mode via Class, Not Media Query

Use `data-theme="dark"` on the `<html>` element for dark mode. This enables user-controlled dark mode (system preference) AND manual override without conflict. The class approach also makes dark mode testable in CI.

```css
[data-theme="dark"] .card {
  background-color: var(--color-surface);
  border-color: oklch(from var(--color-text) l c h / 0.12);
}
```

### 5. Spring Easing for Interactivity

The `cubic-bezier(0.16, 1, 0.3, 1)` spring easing is the single most impactful animation token. It makes UI feel alive rather than mechanical. Use it for: hover states, button presses, toggles, tooltips, drawer/modal entrances. Never use `ease-in-out` for interactive elements — it's mushy.

### 6. 44×44px Touch Targets

WCAG 2.1 Level AAA and Apple HIG require a minimum 44×44px touch target. This is non-negotiable for mobile. Enforce it with `min-height: 44px` and `min-width: 44px` on all interactive elements.

### 7. Reduced Motion by Default

Always wrap animations in `prefers-reduced-motion`. Users with vestibular disorders can experience nausea from motion. The reduced-motion override zeros out all durations and easing, leaving the layout intact.

---

## File Relationships

```
TOKENS.md
├── Primitive palette (raw OKLCH values)
├── Semantic aliases (component-level tokens)
├── Dark mode token map
└── Tailwind theme.extend config

COMPONENTS.md
├── Uses tokens from TOKENS.md
├── Card ──────────── surface, border, shadow, radius, spacing
├── Button ────────── surface, border, text, shadow, duration
├── Form Inputs ───── border, text, error, radius, spacing
├── Badge ─────────── surface (status colors from TOKENS)
├── Avatar ────────── surface, radius
├── Skeleton ──────── surface, skeleton colors, duration
└── Toast ─────────── surface, border, shadow (sonner classNames)

MOTION.md
├── Duration tokens (from TOKENS.md)
├── Easing tokens (from TOKENS.md)
├── Micro-interactions ──── Button, Toggle, Input
├── Scroll reveal ───────── IntersectionObserver
├── Page transitions ────── Fade+slide, Modal, Drawer
└── Reduced motion ──────── duration-zero + ease-default

LAYOUT.md
├── Width tokens (from TOKENS.md — spacing scale)
├── CSS Grid ──────────────── gap tokens, columns
├── Subgrid ───────────────── component-level grid
├── Container Queries ─────── inline-size containers
├── Section Rhythm ───────── spacing scale for sections
└── Forbidden Patterns ────── what NOT to do
```

---

## Implementation Priority

When implementing a new feature using this system:

1. **Start with TOKENS.md** — ensure the tokens you need exist as semantic aliases
2. **Build layout** with LAYOUT.md grid/subgrid patterns before touching components
3. **Implement motion** last — it's the polish layer and depends on everything else
4. **Validate** with the Motion Checklist and Layout Checklist before shipping

---

## Dark Mode Mapping

All tokens have light and dark variants. The mapping is defined in `TOKENS.md` § Dark Mode Token Map.

| Token | Light | Dark |
|---|---|---|
| `--color-surface` | `oklch(98% 0 0)` | `oklch(14% 0 0)` |
| `--color-surface-offset` | `oklch(96% 0 0)` | `oklch(18% 0 0)` |
| `--color-border` | `oklch(from --color-text l c h / 0.08)` | `oklch(from --color-text l c h / 0.12)` |
| `--color-text` | `oklch(25% 0 0)` | `oklch(95% 0 0)` |
| `--color-text-muted` | `oklch(50% 0 0)` | `oklch(65% 0 0)` |
| `--color-skeleton` | `oklch(92% 0 0)` | `oklch(22% 0 0)` |
| `--color-skeleton-shine` | `oklch(96% 0 0)` | `oklch(28% 0 0)` |
| Shadow (light) | Warm amber tint | Cool dark tint |
| Shadow (dark) | Near-black | Deep navy tint |

---

## Accessibility Targets

| Standard | Requirement |
|---|---|
| WCAG 2.1 AA | 4.5:1 contrast for body text, 3:1 for large text |
| WCAG 2.1 AAA | 7:1 contrast for body text, 4.5:1 for large text |
| Apple HIG | 44×44px minimum touch target |
| Focus ring | 3px solid primary, 2px offset (`:focus-visible`) |

---

## Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Styling | Tailwind CSS v4 + CSS variables | Use `theme.extend` for token aliases |
| Animation (micro) | tailwindcss-motion | CSS-only, zero JS overhead |
| Animation (complex) | Framer Motion v11+ | Layout animations, page transitions, gestures |
| Scroll effects | GSAP + ScrollTrigger | Parallax, timeline-based reveals |
| Component primitives | Radix UI | Accessible, unstyled, composable |
| UI library | shadcn/ui | Radix + Tailwind, copy-paste, not a package |
| Command palette | cmdk | Fast, composable, accessible |
| Toast | sonner | Emil Kowalski's toast — the best DX |
| Drawer | vaul | Emil Kowalski's drawer — spring physics |
| Icons | Lucide React | Consistent, tree-shakeable |
| Fonts | Google Fonts (Inter / Geist variants) | Self-hosted via `next/font` |

---

## Adding New Components

When adding a new component to this system:

1. **Check TOKENS.md** — ensure the semantic tokens you need exist
2. **Follow the Component Template:**

```tsx
interface NewComponentProps {
  children: React.ReactNode;
  variant?: 'default' | 'active' | 'disabled';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function NewComponent({
  children,
  variant = 'default',
  size = 'md',
  className = '',
}: NewComponentProps) {
  return (
    <div
      className={cn(
        // Base: surface + border + radius from tokens
        'bg-surface border border-border rounded-lg',
        // Variant: interactive states use --ease-spring
        'transition-all duration-fast ease-spring',
        // Hover, active, disabled states
        'hover:-translate-y-px hover:shadow-md',
        'active:translate-y-0 active:scale-[0.99]',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        // Size tokens
        size === 'sm' && 'p-3 text-sm',
        size === 'md' && 'p-4 text-base',
        size === 'lg' && 'p-6 text-lg',
        className
      )}
    >
      {children}
    </div>
  );
}
```

3. **Document the component** in `COMPONENTS.md` with the three sections:
   - Design Rules (token usage, constraints)
   - CSS/Tailwind implementation
   - React/TSX with props interface
   - Dark mode variant if applicable

4. **Add motion** using `--ease-spring` + `--duration-fast` for all interactive states

5. **Validate** the motion checklist in `MOTION.md`

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2026-04-16 | Initial design system — OKLCH palette, fluid type, component patterns, spring motion, grid layout |

---

*This design system was synthesized from the Linear / Vercel / Stripe production quality design level. All tokens, patterns, and principles are meant to be implementation-ready for React/Next.js projects using Tailwind CSS v4.*

*Maintained by: Bashara + Legion | Last compiled: 2026-04-16*
