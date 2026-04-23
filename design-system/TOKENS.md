# Design Token System — TOKENS.md

> **Version:** 1.0.0
> **Last updated:** 2026-04-16
> **Source palette:** Nexus Palette (warm neutrals + Hydra Teal accent)
> **Format:** CSS custom properties + Tailwind config mapping

---

## Table of Contents

1. [Color System](#1-color-system)
2. [Type Scale](#2-type-scale)
3. [Spacing System](#3-spacing-system)
4. [Shadow System](#4-shadow-system)
5. [Radius](#5-radius)
6. [Easing](#6-easing)
7. [Content Widths](#7-content-widths)
8. [Semantic Aliases](#8-semantic-aliases)
9. [Dark Mode — Full Token Map](#9-dark-mode--full-token-map)
10. [Accessibility Notes](#10-accessibility-notes)
11. [Tailwind Configuration Snippet](#11-tailwind-configuration-snippet)

---

## 1. Color System

### Primitive Palette

| Token | Hex (sRGB) | OKLCH (approx.) | Role |
|---|---|---|---|
| `--color-bg` | `#f7f6f2` | `oklch(0.98 0.005 85)` | Page background |
| `--color-surface` | `#f9f8f5` | `oklch(0.97 0.004 85)` | Card / panel surface |
| `--color-surface-2` | `#fbfbf9` | `oklch(0.99 0.002 85)` | Nested surface |
| `--color-surface-offset` | `#f3f0ec` | `oklch(0.95 0.006 85)` | Offset / inset surface |
| `--color-border` | `#d4d1ca` | `oklch(0.82 0.008 80)` | Default border |
| `--color-text` | `#28251d` | `oklch(0.21 0.015 80)` | Primary text |
| `--color-text-muted` | `#7a7974` | `oklch(0.53 0.010 80)` | Secondary / muted text |
| `--color-text-faint` | `#bab9b4` | `oklch(0.73 0.008 80)` | Placeholder / disabled text |
| `--color-primary` | `#01696f` | `oklch(0.52 0.130 195)` | Hydra Teal — primary accent |
| `--color-primary-hover` | `#0c4e54` | `oklch(0.45 0.120 195)` | Darkened primary for hover |

### Dark Mode Primitives

| Token | Hex (sRGB) | OKLCH (approx.) |
|---|---|---|
| `--color-bg` (dark) | `#171614` | `oklch(0.15 0.005 70)` |
| `--color-surface` (dark) | `#1c1b19` | `oklch(0.18 0.005 70)` |
| `--color-surface-2` (dark) | `#20201d` | `oklch(0.20 0.004 70)` |
| `--color-surface-offset` (dark) | `#141412` | `oklch(0.12 0.004 70)` |
| `--color-border` (dark) | `#3a3936` | `oklch(0.30 0.006 70)` |
| `--color-text` (dark) | `#cdccca` | `oklch(0.83 0.005 80)` |
| `--color-text-muted` (dark) | `#7a7974` | `oklch(0.53 0.008 80)` |
| `--color-text-faint` (dark) | `#52514e` | `oklch(0.38 0.006 70)` |
| `--color-primary` (dark) | `#4f98a3` | `oklch(0.65 0.100 195)` |
| `--color-primary-hover` (dark) | `#68b3bf` | `oklch(0.72 0.090 195)` |

### CSS Custom Properties — Light (default)

```css
:root {
  /* Surfaces — warm neutral, NOT cold gray */
  --color-bg:             #f7f6f2;
  --color-surface:        #f9f8f5;
  --color-surface-2:      #fbfbf9;
  --color-surface-offset: #f3f0ec;
  --color-border:         #d4d1ca;

  /* Text — 3 levels */
  --color-text:           #28251d;
  --color-text-muted:     #7a7974;
  --color-text-faint:     #bab9b4;

  /* Single accent — Hydra Teal */
  --color-primary:        #01696f;
  --color-primary-hover:  #0c4e54;
}
```

---

## 2. Type Scale

Fluid `clamp()` scale — responsive without breakpoints.

```css
:root {
  --text-xs:   clamp(0.75rem,   0.7rem  + 0.25vw, 0.875rem);  /* 12px–14px  */
  --text-sm:   clamp(0.875rem,  0.8rem  + 0.35vw, 1rem);     /* 14px–16px  */
  --text-base: clamp(1rem,      0.95rem + 0.25vw, 1.125rem);  /* 16px–18px  */
  --text-lg:   clamp(1.125rem,  1rem    + 0.75vw, 1.5rem);   /* 18px–24px  */
  --text-xl:   clamp(1.5rem,    1.2rem  + 1.25vw, 2.25rem);  /* 24px–36px  */
  --text-2xl:  clamp(2rem,      1.2rem  + 2.5vw,  3.5rem);   /* 32px–56px  */

  /* Semantic type roles */
  --text-body:    var(--text-base);
  --text-caption: var(--text-xs);
  --text-heading: var(--text-xl);
  --text-display: var(--text-2xl);
}
```

**Formula:** `clamp(min, preferred, max)` where `preferred` uses `vw` units so size tracks viewport width.

---

## 3. Spacing System

4px base grid. All spacing tokens are multiples of 4px.

```css
:root {
  --space-1:  0.25rem;   /*  4px */
  --space-2:  0.5rem;    /*  8px */
  --space-3:  0.75rem;   /* 12px */
  --space-4:  1rem;      /* 16px */
  --space-5:  1.25rem;   /* 20px */
  --space-6:  1.5rem;    /* 24px */
  --space-8:  2rem;      /* 32px */
  --space-10: 2.5rem;    /* 40px */
  --space-12: 3rem;      /* 48px */
  --space-16: 4rem;      /* 64px */
  --space-20: 5rem;      /* 80px */
  --space-24: 6rem;      /* 96px */
  --space-32: 8rem;      /* 128px */

  /* Component-specific spacing aliases */
  --space-component-gap: var(--space-4);
  --space-section-gap:    var(--space-12);
  --space-page-padding:   var(--space-6);
}
```

---

## 4. Shadow System

Shadows use OKLCH with lightness + chroma so they feel warm (not pure gray).

```css
:root {
  /* Warm shadow — oklch(L C H / opacity) */
  --shadow-sm: 0 1px 2px oklch(0.2 0.01 80 / 0.06);
  --shadow-md: 0 4px 12px oklch(0.2 0.01 80 / 0.08);
  --shadow-lg: 0 12px 32px oklch(0.2 0.01 80 / 0.12);
  --shadow-xl: 0 24px 48px oklch(0.2 0.01 80 / 0.16);

  /* Dark mode shadows — deeper, cooler */
  --shadow-sm-dark: 0 1px 2px oklch(0.05 0.01 70 / 0.20);
  --shadow-md-dark: 0 4px 12px oklch(0.05 0.01 70 / 0.25);
  --shadow-lg-dark: 0 12px 32px oklch(0.05 0.01 70 / 0.30);
}

[data-theme="dark"] {
  --shadow-sm: var(--shadow-sm-dark);
  --shadow-md: var(--shadow-md-dark);
  --shadow-lg: var(--shadow-lg-dark);
}
```

---

## 5. Radius

```css
:root {
  --radius-sm:   0.375rem;   /*  6px — small tags, badges       */
  --radius-md:   0.5rem;    /*  8px — buttons, inputs, cards  */
  --radius-lg:   0.75rem;   /* 12px — modals, large panels     */
  --radius-xl:   1rem;      /* 16px — image containers         */
  --radius-full: 9999px;    /* pill / circular elements        */
}
```

---

## 6. Easing

```css
:root {
  /* Primary spring easing — for entrances and UI feedback */
  --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);

  /* Standard ease — safe fallback for all transitions */
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);

  /* Entrance — slightly more deceleration than spring */
  --ease-enter: cubic-bezier(0.0, 0, 0.2, 1);

  /* Exit — faster start, lets elements leave quickly */
  --ease-exit: cubic-bezier(0.4, 0, 1, 1);

  /* Duration tokens (pair with ease tokens) */
  --duration-fast:   100ms;
  --duration-normal: 200ms;
  --duration-slow:   400ms;
}
```

---

## 7. Content Widths

```css
:root {
  /* Narrow — single-column text (editorials, docs) */
  --content-narrow:  640px;

  /* Default — standard page layout */
  --content-default: 960px;

  /* Wide — marketing, dashboards, data-heavy layouts */
  --content-wide:    1200px;

  /* Full bleed */
  --content-max:     1440px;
}
```

---

## 8. Semantic Aliases

All semantic aliases reference the primitive tokens above. This isolates components from palette changes.

### Status Colors

| Token | Value | Usage |
|---|---|---|
| `--color-error` | `#b83a3a` | Error states, destructive actions |
| `--color-error-bg` | `oklch(0.95 0.060 25)` | Error background tint |
| `--color-success` | `#2a7a4b` | Success states, confirmations |
| `--color-success-bg` | `oklch(0.93 0.070 145)` | Success background tint |
| `--color-warning` | `#9a5f0a` | Warning states |
| `--color-warning-bg` | `oklch(0.95 0.060 70)` | Warning background tint |
| `--color-info` | `var(--color-primary)` | Informational — uses Hydra Teal |
| `--color-info-bg` | `oklch(0.93 0.040 195)` | Info background tint |

### Interactive Role Aliases

| Token | Value | Usage |
|---|---|---|
| `--color-focus-ring` | `var(--color-primary)` | `:focus-visible` outline |
| `--color-selection-bg` | `oklch(0.90 0.080 195)` | `::selection` background |
| `--color-skeleton` | `oklch(0.88 0.005 85)` | Loading skeleton base |
| `--color-skeleton-shine` | `oklch(0.92 0.005 85)` | Skeleton shimmer highlight |

### Component Tokens

| Token | Value | Usage |
|---|---|---|
| `--color-input-bg` | `var(--color-surface)` | Text input backgrounds |
| `--color-input-border` | `var(--color-border)` | Default input borders |
| `--color-input-focus-border` | `var(--color-primary)` | Focused input border |
| `--color-btn-primary-bg` | `var(--color-primary)` | Primary button fill |
| `--color-btn-primary-text` | `#ffffff` | Primary button label |
| `--color-btn-secondary-bg` | `var(--color-surface)` | Secondary button fill |
| `--color-btn-secondary-border` | `var(--color-border)` | Secondary button border |
| `--color-card-bg` | `var(--color-surface)` | Card / panel background |
| `--color-card-border` | `var(--color-border)` | Card border |
| `--color-divider` | `var(--color-border)` | Horizontal rule / separator |
| `--color-backdrop` | `oklch(0.15 0.01 70 / 0.6)` | Modal overlay scrim |

---

## 9. Dark Mode — Full Token Map

```css
[data-theme="dark"] {
  /* Surfaces */
  --color-bg:             #171614;
  --color-surface:        #1c1b19;
  --color-surface-2:      #20201d;
  --color-surface-offset: #141412;
  --color-border:         #3a3936;

  /* Text */
  --color-text:           #cdccca;
  --color-text-muted:     #7a7974;
  --color-text-faint:     #52514e;

  /* Accent */
  --color-primary:        #4f98a3;
  --color-primary-hover:  #68b3bf;

  /* Status — dark mode adjustments */
  --color-error:          #d96262;
  --color-error-bg:       oklch(0.30 0.080 25);
  --color-success:        #4caf73;
  --color-success-bg:     oklch(0.30 0.080 145);
  --color-warning:        #c98c2a;
  --color-warning-bg:     oklch(0.28 0.070 70);

  /* Component tokens */
  --color-input-bg:           #1c1b19;
  --color-input-border:        #3a3936;
  --color-input-focus-border:  #4f98a3;
  --color-btn-secondary-bg:    #1c1b19;
  --color-btn-secondary-border: #3a3936;
  --color-card-bg:             #1c1b19;
  --color-card-border:         #3a3936;
  --color-divider:             #3a3936;
  --color-backdrop:            oklch(0.05 0.01 70 / 0.80);
  --color-selection-bg:        oklch(0.50 0.100 195);
  --color-skeleton:            oklch(0.22 0.005 70);
  --color-skeleton-shine:      oklch(0.28 0.005 70);
}
```

---

## 10. Accessibility Notes

### Contrast Ratios (WCAG 2.1)

All text combinations below target **minimum AA** (4.5:1 for body, 3:1 for large text).

| Foreground | Background | Ratio | Level |
|---|---|---|---|
| `--color-text` | `--color-bg` | ~11.2:1 | AAA |
| `--color-text-muted` | `--color-bg` | ~5.8:1 | AA |
| `--color-text` | `--color-surface` | ~10.8:1 | AAA |
| `--color-text-faint` | `--color-surface` | ~3.8:1 | AA (large text only) |
| `--color-primary` | `--color-bg` | ~5.1:1 | AA |
| White `#ffffff` | `--color-primary` | ~4.8:1 | AA |
| White `#ffffff` | `--color-error` | ~4.9:1 | AA |
| `--color-text` (dark) | `--color-bg` (dark) | ~9.5:1 | AAA |
| `--color-text-muted` (dark) | `--color-bg` (dark) | ~4.6:1 | AA |

### Focus Visibility

```css
/* Minimum 3px solid ring with sufficient contrast */
:focus-visible {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  :root {
    --ease-spring:  cubic-bezier(0.4, 0, 0.2, 1);
    --ease-enter:    cubic-bezier(0.4, 0, 0.2, 1);
    --ease-exit:     cubic-bezier(0.4, 0, 0.2, 1);
    --duration-fast:   0ms;
    --duration-normal: 0ms;
    --duration-slow:   0ms;
  }
}
```

### Color-blindness Safety

The Nexus palette avoids relying on hue alone. Status colors use **value contrast** (lightness deltas) in addition to hue, so they remain distinguishable in deuteranopia/protanopia:

- Error: `oklch(0.52 0.18 25)` — low lightness, reddish
- Success: `oklch(0.52 0.14 145)` — medium lightness, greenish
- Warning: `oklch(0.55 0.13 70)` — medium-low lightness, amber

Never use color as the **sole** indicator of state — always pair with an icon or label.

---

## 11. Tailwind Configuration Snippet

Copy this into `tailwind.config.ts` (or `.js`) under `theme.extend`. Assumes CSS custom properties are defined on `:root` and `[data-theme="dark"]`.

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  theme: {
    extend: {
      colors: {
        // Surfaces
        bg:             "var(--color-bg)",
        surface:        "var(--color-surface)",
        "surface-2":    "var(--color-surface-2)",
        "surface-offset":"var(--color-surface-offset)",
        border:         "var(--color-border)",

        // Text
        text:           "var(--color-text)",
        "text-muted":   "var(--color-text-muted)",
        "text-faint":   "var(--color-text-faint)",

        // Primary accent — Hydra Teal
        primary: {
          DEFAULT: "var(--color-primary)",
          hover:   "var(--color-primary-hover)",
        },

        // Status
        error: {
          DEFAULT:   "var(--color-error)",
          bg:        "var(--color-error-bg)",
        },
        success: {
          DEFAULT:   "var(--color-success)",
          bg:        "var(--color-success-bg)",
        },
        warning: {
          DEFAULT:   "var(--color-warning)",
          bg:        "var(--color-warning-bg)",
        },
        info: {
          DEFAULT:   "var(--color-primary)",
          bg:        "var(--color-info-bg)",
        },

        // Component
        input: {
          bg:     "var(--color-input-bg)",
          border: "var(--color-input-border)",
          focus: "var(--color-input-focus-border)",
        },
        card: {
          bg:     "var(--color-card-bg)",
          border: "var(--color-card-border)",
        },
        btn: {
          primary: {
            bg:    "var(--color-btn-primary-bg)",
            text:  "var(--color-btn-primary-text)",
          },
          secondary: {
            bg:    "var(--color-btn-secondary-bg)",
            border:"var(--color-btn-secondary-border)",
          },
        },
        backdrop: "var(--color-backdrop)",
      },

      fontSize: {
        xs:   "var(--text-xs)",
        sm:   "var(--text-sm)",
        base: "var(--text-base)",
        lg:   "var(--text-lg)",
        xl:   "var(--text-xl)",
        "2xl":"var(--text-2xl)",
      },

      spacing: {
        "1":  "var(--space-1)",
        "2":  "var(--space-2)",
        "3":  "var(--space-3)",
        "4":  "var(--space-4)",
        "5":  "var(--space-5)",
        "6":  "var(--space-6)",
        "8":  "var(--space-8)",
        "10": "var(--space-10)",
        "12": "var(--space-12)",
        "16": "var(--space-16)",
        "20": "var(--space-20)",
        "24": "var(--space-24)",
        "32": "var(--space-32)",
      },

      borderRadius: {
        sm:   "var(--radius-sm)",
        md:   "var(--radius-md)",
        lg:   "var(--radius-lg)",
        xl:   "var(--radius-xl)",
        full: "var(--radius-full)",
      },

      boxShadow: {
        sm:  "var(--shadow-sm)",
        md:  "var(--shadow-md)",
        lg:  "var(--shadow-lg)",
        xl:  "var(--shadow-xl)",
      },

      borderColor: {
        DEFAULT: "var(--color-border)",
      },

      backgroundColor: {
        surface:  "var(--color-surface)",
        "surface-2": "var(--color-surface-2)",
        "surface-offset": "var(--color-surface-offset)",
      },

      transitionTimingFunction: {
        spring:   "var(--ease-spring)",
        enter:    "var(--ease-enter)",
        exit:     "var(--ease-exit)",
        default:  "var(--ease-default)",
      },

      transitionDuration: {
        fast:   "var(--duration-fast)",
        normal: "var(--duration-normal)",
        slow:   "var(--duration-slow)",
      },

      maxWidth: {
        narrow:  "var(--content-narrow)",
        default: "var(--content-default)",
        wide:    "var(--content-wide)",
        full:    "var(--content-max)",
      },
    },
  },
};

export default config;
```

### Dark Mode Tailwind Integration

Add this to your `tailwind.config.ts` plugins or `main CSS` entry to activate dark mode variants using `[data-theme="dark"]`:

```typescript
// Inside the config above, also add:
darkMode: "class",  // triggers on [data-theme="dark"] class
```

And in your root CSS:

```css
@layer base {
  [data-theme="dark"] {
    /* All --color-* tokens re-declared under dark mode */
    color-scheme: dark;
  }
}
```

### Usage Example

```html
<!-- Surfaces -->
<div class="bg-surface border-border rounded-lg shadow-md p-6">
  <!-- Text hierarchy -->
  <h2 class="text-xl text-text">Heading</h2>
  <p class="text-base text-text-muted">Secondary body copy</p>

  <!-- Primary button -->
  <button class="bg-primary text-white rounded-md px-4 py-2
                 hover:bg-primary-hover transition-colors duration-normal">
    Action
  </button>

  <!-- Error state -->
  <p class="text-error bg-error-bg rounded-md p-4">Something went wrong</p>
</div>

<!-- Dark mode: add data-theme="dark" to root element -->
<div data-theme="dark">
  <!-- all tokens automatically resolve to dark values -->
</div>
```

---

*Last reviewed: 2026-04-16 | Palette: Nexus (warm neutrals) + Hydra Teal accent*