# Layout System — LAYOUT.md

> **Version:** 1.0.0 | **Last updated:** 2026-04-16
> **Design level:** Linear / Vercel / Stripe production quality

---

## Table of Contents

1. [Content Widths](#1-content-widths)
2. [CSS Grid System](#2-css-grid-system)
3. [Subgrid](#3-subgrid)
4. [Container Queries](#4-container-queries)
5. [Mobile-First Rules](#5-mobile-first-rules)
6. [Section Rhythm](#6-section-rhythm)
7. [Forbidden Patterns](#7-forbidden-patterns)
8. [Layout Checklist](#8-layout-checklist)

---

## 1. Content Widths

Content width tokens control maximum line lengths for readability.

### Width Tokens

```css
:root {
  /* Content widths */
  --width-narrow:   640px;   /* Single-column text, tight UI    */
  --width-default:  768px;   /* Standard prose, cards            */
  --width-wide:    1024px;   /* Dashboard, multi-column layouts  */
  --width-max:     1280px;   /* Page max — outer container       */

  /* Text measure (optimal line length) */
  --measure-xs:    20ch;    /* Labels, short strings    */
  --measure-sm:    30ch;    /* Badges, buttons          */
  --measure-md:    45ch;    /* Body text, paragraphs     */
  --measure-lg:    60ch;    /* Long-form prose          */
  --measure-xl:    72ch;    /* Maximum comfortable      */
}
```

### Usage

```css
.article-body {
  max-width: var(--width-narrow);
  margin-inline: auto;
}

.prose {
  max-width: var(--measure-lg);
}

.card-grid {
  max-width: var(--width-wide);
  margin-inline: auto;
}
```

### Semantic Aliases

```css
.container-narrow  { max-width: var(--width-narrow); }
.container-default { max-width: var(--width-default); }
.container-wide    { max-width: var(--width-wide);    }
.container-max     { max-width: var(--width-max);     }
```

---

## 2. CSS Grid System

### Base Grid

```css
.grid {
  display: grid;
  gap: var(--space-6);
}

/* Columns */
.grid-cols-1  { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-2  { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-3  { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-4  { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.grid-cols-6  { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.grid-cols-12 { grid-template-columns: repeat(12, minmax(0, 1fr)); }

/* Auto-fit / auto-fill helpers */
.grid-auto     { grid-template-columns: repeat(auto-fit, minmax(var(--space-64), 1fr)); }
.grid-auto-sm  { grid-template-columns: repeat(auto-fit, minmax(var(--space-48), 1fr)); }
.grid-auto-lg  { grid-template-columns: repeat(auto-fit, minmax(var(--space-80), 1fr)); }
```

### Column Span Utilities

```css
.col-span-full  { grid-column: 1 / -1; }
.col-span-2     { grid-column: span 2 / span 2; }
.col-span-3     { grid-column: span 3 / span 3; }
.col-span-4     { grid-column: span 4 / span 4; }
.col-span-6     { grid-column: span 6 / span 6; }
.col-span-8     { grid-column: span 8 / span 8; }

/* Start position */
.col-start-1  { grid-column-start: 1; }
.col-start-2  { grid-column-start: 2; }
.col-start-3  { grid-column-start: 3; }
.col-start-auto { grid-column-start: auto; }
```

### Row Span Utilities

```css
.row-span-2    { grid-row: span 2 / span 2; }
.row-span-3    { grid-row: span 3 / span 3; }
.row-span-full { grid-row: 1 / -1; }
```

### Gutters

```css
.gap-0   { gap: 0; }
.gap-1   { gap: var(--space-1); }
.gap-2   { gap: var(--space-2); }
.gap-3   { gap: var(--space-3); }
.gap-4   { gap: var(--space-4); }
.gap-6   { gap: var(--space-6); }
.gap-8   { gap: var(--space-8); }

/* Axis-specific */
.gap-x-4  { column-gap: var(--space-4); }
.gap-y-6  { row-gap: var(--space-6); }
```

---

## 3. Subgrid

Subgrid allows nested elements to align to the parent grid track. Use it for card interiors that need to align to an outer grid.

### When to Use Subgrid

- Card grids where card content columns must align across cards
- Form layouts where labels and inputs need to track together
- Dashboard widgets that share alignment with the outer layout

### Basic Subgrid Pattern

```css
.parent-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
}

.card {
  display: grid;
  grid-template-columns: subgrid; /* Inherits 3 columns from parent */
  grid-row: span 3;               /* Card spans 3 rows if needed */
  gap: var(--space-4);
}

.card-header {
  grid-column: 1 / -1; /* Spans all 3 columns */
}

.card-body {
  grid-column: 1 / 2;  /* First column of the subgrid */
}

.card-media {
  grid-column: 2 / 4;  /* Last 2 columns */
}
```

### Form Subgrid

```css
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-6);
}

.form-row {
  display: grid;
  grid-template-columns: subgrid;
  grid-column: 1 / -1; /* Spans full width */
  gap: var(--space-4);
}
```

### Fallback for Unsupported Browsers

```css
@supports not (grid-template-columns: subgrid) {
  .card {
    display: flex;
    flex-direction: column;
  }
  .card-header,
  .card-body,
  .card-media {
    width: 100%;
  }
}
```

---

## 4. Container Queries

Container queries respond to the parent container's width, not the viewport. Use them for truly modular components.

### Setup

```css
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}
```

### Query Syntax

```css
@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 200px 1fr;
  }
}

@container card (min-width: 700px) {
  .card {
    grid-template-columns: 240px 1fr 200px;
  }
}

@container card (max-width: 399px) {
  .card-body {
    display: none; /* Simplify on small containers */
  }
}
```

### Container Query Units

```css
.cqi-1  { width: 1cqi;  }  /* 1% of container inline size */
.cqi-2  { width: 2cqi;  }
.cqi-3  { width: 3cqi;  }
.cqi-4  { width: 4cqi;  }
.cqi-5  { width: 5cqi;  }
```

### Card Component with Container Queries

```css
/* Base: stacked layout */
.responsive-card {
  container-type: inline-size;
  container-name: card;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* Side-by-side when container ≥ 400px */
@container card (min-width: 400px) {
  .responsive-card {
    flex-direction: row;
    align-items: center;
  }
  .card-media {
    width: 40%;
  }
  .card-content {
    flex: 1;
  }
}
```

---

## 5. Mobile-First Rules

### Breakpoints

```css
/* Mobile: 375px — design for this first */
.sm\:  640px;   /* Landscape phones, small tablets */
.md\:  768px;   /* Tablets */
.lg\: 1024px;   /* Laptops */
.xl\: 1280px;   /* Desktops */
.2xl\:1536px;   /* Large screens */

/* Tailwind integration */
@media (min-width: 640px)  { .sm\:block { display: block; } }
@media (min-width: 768px)  { .md\:block { display: block; } }
@media (min-width: 1024px) { .lg\:block { display: block; } }
@media (min-width: 1280px) { .xl\:block { display: block; } }
```

### Design Baseline

Design at **375px mobile** first. This forces content hierarchy discipline.

```css
/* Mobile base — never set a min-width here */
.page-section {
  padding: var(--space-6) var(--space-4);
}

/* Tablet+ */
@media (min-width: 768px) {
  .page-section {
    padding: var(--space-8) var(--space-6);
  }
}

/* Desktop+ */
@media (min-width: 1024px) {
  .page-section {
    padding: var(--space-12) var(--space-8);
  }
}
```

### Touch Targets

**Minimum 44×44px on all touch targets** (WCAG 2.1 AAA / Apple HIG).

```css
.btn {
  min-height: 44px;
  min-width: 44px;
}

.icon-btn {
  min-height: 44px;
  min-width: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
```

### Interactive Zones

```css
.list-item-interactive {
  min-height: 48px;      /* Extra breathing room for list rows */
  padding: var(--space-3) var(--space-4);
}

.table-row {
  min-height: 52px;      /* Table rows need generous hit area */
}
```

---

## 6. Section Rhythm

Sections create visual pacing. Vary rhythm to avoid monotony — not every section needs the same padding.

### Section Scale

```css
.section-xs  { padding-block: var(--space-4);  }
.section-sm  { padding-block: var(--space-6);  }
.section-md  { padding-block: var(--space-8);  }
.section-lg  { padding-block: var(--space-12); }
.section-xl  { padding-block: var(--space-16); }
.section-2xl { padding-block: var(--space-24); }
```

### Rhythm Pattern

Alternate section intensity to create visual interest:

```css
.hero     { padding-block: var(--section-2xl); }  /* Dramatic opening */
.features { padding-block: var(--section-lg);  }   /* Dense information */
.pricing  { padding-block: var(--section-xl);  }   /* Breathing room */
.cta      { padding-block: var(--section-2xl); }    /* Dramatic close */
```

### Component Inner Spacing

```css
.section-inner {
  max-width: var(--width-max);
  margin-inline: auto;
  padding-inline: var(--space-4);
}

@media (min-width: 768px) {
  .section-inner {
    padding-inline: var(--space-6);
  }
}

@media (min-width: 1024px) {
  .section-inner {
    padding-inline: var(--space-8);
  }
}
```

---

## 7. Forbidden Patterns

These patterns are banned. If you catch yourself using one, redesign.

### ❌ 3-Column Equal Grid

```css
/* WRONG — 3 equal columns collapse poorly on tablet */
.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* Breaks at 768px */
}
```

```css
/* RIGHT — auto-fit with minmax prevents collapse */
.grid-auto-3 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
}
```

### ❌ Centered Everything

```css
/* WRONG — centered single column is never the answer */
.center-all {
  display: flex;
  align-items: center;
  justify-content: center;
}
```

Reserve centering for: modals, empty states, single-call-to-action pages, loading states.

### ❌ Cookie-Cutter Section Order

Not every section follows the same pattern: heading → subheading → 3 cards → CTA button.

Vary the order. Examples:
- Lead with social proof before explaining features
- Put a bold statement or quote at the top, not a heading
- Use a full-bleed media break between text sections
- Alternate between wide and narrow content widths

### ❌ Colored Side-Borders on Cards

```css
/* WRONG — colored left borders are a dated pattern */
.card-with-border {
  border-left: 4px solid var(--color-primary); /* Looks like status bar */
}
```

```css
/* RIGHT — surface elevation with badge for status */
.card {
  background: var(--color-surface);
  border: 1px solid oklch(from var(--color-text) l c h / 0.08);
  border-radius: var(--radius-lg);
}

.card-status {
  /* Badge instead of border communicates status clearly */
}
```

### ❌ Aspect Ratio Boxes for Decoration

```css
/* WRONG — hardcoded aspect ratios break responsiveness */
.decorative-box {
  aspect-ratio: 16 / 9; /* May not fit content */
}
```

Use `aspect-ratio` only for embedded media (images, videos, iframes). Never for decorative containers.

---

## 8. Layout Checklist

Before shipping any layout, run through this:

- [ ] **Content widths** — All prose blocks respect `--measure-lg` (60ch max)
- [ ] **Grid system** — Used `auto-fit minmax()` instead of fixed columns
- [ ] **Subgrid** — Used where card interiors need outer grid alignment
- [ ] **Container queries** — Used for modular components that live in varying contexts
- [ ] **Mobile-first** — Base styles are mobile; `min-width` breakpoints only add complexity
- [ ] **Touch targets** — All interactive elements ≥ 44×44px
- [ ] **Section rhythm** — Varied section padding creates visual pacing
- [ ] **No forbidden patterns** — No 3-column equal grid, no centered-everything, no card borders
- [ ] **Responsive images** — `srcset` or `image-set` for all raster images
- [ ] **No layout jank** — No `width: 100%` combined with `margin-inline: auto` on same element
- [ ] **Content never overflows** — Tested at 320px minimum

---

*Last reviewed: 2026-04-16 | Grid pattern source: Linear design system, CSS Grid Level 2 spec*
