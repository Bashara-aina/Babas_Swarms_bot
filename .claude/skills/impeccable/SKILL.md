---
name: impeccable
description: "Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, distill, harden, optimize, adapt, animate, colorize, extract, or otherwise improve a frontend interface. Covers websites, landing pages, dashboards, product UI, app shells, components, forms, settings, onboarding, and empty states. Handles UX review, visual hierarchy, information architecture, cognitive load, accessibility, performance, responsive behavior, theming, anti-patterns, typography, fonts, spacing, layout, alignment, color, motion, micro-interactions, UX copy, error states, edge cases, i18n, and reusable design systems or tokens. Also use for bland designs that need to become bolder or more delightful, loud designs that should become quieter, live browser iteration on UI elements, or ambitious visual effects that should feel technically extraordinary. Not for backend-only or non-UI tasks."
argument-hint: "[command] [target]"
user-invocable: true
allowed-tools:
  - Bash(npx impeccable *)
license: Apache 2.0
---

Designs and iterates production-grade frontend interfaces. Real working code, committed design choices, exceptional craft.

## Setup

You MUST do these steps before proceeding:

1. Run `node ./scripts/context.mjs` once per session. If you've already seen its output, do not re-run. If it reports `NO_PRODUCT_MD`, stop and follow `reference/init.md` before anything else.
2. If the user invoked a sub-command (`craft`, `shape`, `audit`, `polish`, ...), read `reference/<command>.md` next. Non-optional.
3. Familiarize yourself with existing design system, conventions, and components. Read at least one project file. Required even with a sub-command reference.
4. Read the matching register reference. If marketing/landing page/portfolio, read `reference/brand.md`. If app UI/admin/dashboard, read `reference/product.md`.
5. If the project is brand-new (no existing CSS tokens/theme), run `node ./scripts/palette.mjs` for a brand seed color. Use OKLCH. Skip if step 3 found committed brand colors.

## Design guidance

Produce ready-to-ship, production-grade code. Every page/section/component must be battle-tested (browser screenshots, computer use, etc).

### General rules — summary

For the full details including color, typography, layout, motion, interaction, and copy rules, read `reference/design-rules.md`.

Key highlights:
- **Color:** Contrast >= 4.5:1 body text. Use OKLCH. No cream/sand/parchment default backgrounds. Pick theme by writing a physical scene sentence.
- **Typography:** Body 65-75ch. Scale ratio >= 1.25. Cap fonts at 3. Hero clamp() max <= 6rem. Letter-spacing floor >= -0.04em.
- **Layout:** Flexbox for 1D, Grid for 2D. Cards are lazy — use sparingly, never nested. Semantic z-index scale.
- **Motion:** Ease-out expo curves. No bounce/elastic. Reduced-motion alternative required. Reveal animations must not gate content visibility.
- **Copy:** Every word earns its place. No em dashes. No marketing buzzwords. Button labels: verb + object.

### Absolute bans

Match-and-refuse. If you're about to write any of these, rewrite with different structure.

- **Side-stripe borders.** `border-left`/`right` >1px as accent on cards, list items, callouts.
- **Gradient text.** `background-clip: text` + gradient. Use solid color, emphasis via weight/size.
- **Glassmorphism as default.** Blurs and glass used decoratively.
- **The hero-metric template.** Big number + small label + stats + gradient accent.
- **Identical card grids.** Same-sized cards with icon + heading + text, repeated endlessly.
- **Tiny uppercase tracked eyebrow above every section.** "ABOUT" "PROCESS" "PRICING" as default scaffolding. One named kicker is voice; on every section is AI grammar.
- **Numbered section markers as default (01 / 02 / 03).** Earn their place when the section is a real sequence.
- **Text that overflows its container.** Test heading copy at every breakpoint; reduce clamp max or rewrite.

Codex-specific (refuse-and-rewrite):
- **`border: 1px solid X` + `box-shadow` with blur >= 16px** on the same element. Pick one.
- **`border-radius: 32px+`** on cards/sections/inputs. Cards top out at 12-16px.
- **Hand-drawn/sketchy SVG illustrations.** `feTurbulence`, `doodle`, crude path scenes. Don't.
- **`repeating-linear-gradient(...)` stripe backgrounds.** Pure decoration. Don't.
- **"X theater" / "actually X" / "not just X, it's Y" copy.** Choose specific nouns.

### The AI slop test

If someone could say "AI made that" without doubt, it's failed.

**First-order check:** Could someone guess the theme + palette from the category alone? If so, rework the scene sentence and color strategy.

**Second-order check:** Could someone guess the aesthetic family from category-plus-anti-references? If so, rework until both answers are not obvious.

## Commands

| Command | Category | Description | Reference |
|---|---|---|---|
| `craft [feature]` | Build | Shape, then build a feature end-to-end | [reference/craft.md](reference/craft.md) |
| `shape [feature]` | Build | Plan UX/UI before writing code | [reference/shape.md](reference/shape.md) |
| `init` | Build | Set up project context | [reference/init.md](reference/init.md) |
| `document` | Build | Generate DESIGN.md from existing code | [reference/document.md](reference/document.md) |
| `extract [target]` | Build | Pull tokens/components into design system | [reference/extract.md](reference/extract.md) |
| `critique [target]` | Evaluate | UX design review with heuristic scoring | [reference/critique.md](reference/critique.md) |
| `audit [target]` | Evaluate | Technical quality (a11y, perf, responsive) | [reference/audit.md](reference/audit.md) |
| `polish [target]` | Refine | Final quality pass before shipping | [reference/polish.md](reference/polish.md) |
| `bolder [target]` | Refine | Amplify safe/bland designs | [reference/bolder.md](reference/bolder.md) |
| `quieter [target]` | Refine | Tone down aggressive designs | [reference/quieter.md](reference/quieter.md) |
| `distill [target]` | Refine | Strip to essence | [reference/distill.md](reference/distill.md) |
| `harden [target]` | Refine | Production-ready (errors, i18n, edge cases) | [reference/harden.md](reference/harden.md) |
| `onboard [target]` | Refine | First-run flows, empty states | [reference/onboard.md](reference/onboard.md) |
| `animate [target]` | Enhance | Add purposeful motion | [reference/animate.md](reference/animate.md) |
| `colorize [target]` | Enhance | Add strategic color | [reference/colorize.md](reference/colorize.md) |
| `typeset [target]` | Enhance | Typography hierarchy | [reference/typeset.md](reference/typeset.md) |
| `layout [target]` | Enhance | Spacing, rhythm, visual hierarchy | [reference/layout.md](reference/layout.md) |
| `delight [target]` | Enhance | Personality and memorable touches | [reference/delight.md](reference/delight.md) |
| `overdrive [target]` | Enhance | Push past conventional limits | [reference/overdrive.md](reference/overdrive.md) |
| `clarify [target]` | Fix | UX copy, labels, error messages | [reference/clarify.md](reference/clarify.md) |
| `adapt [target]` | Fix | Different devices and screen sizes | [reference/adapt.md](reference/adapt.md) |
| `optimize [target]` | Fix | UI performance | [reference/optimize.md](reference/optimize.md) |
| `live` | Iterate | In-browser variant mode | [reference/live.md](reference/live.md) |

### Routing rules

1. **No argument**: make the menu context-aware. Run `node ./scripts/context-signals.mjs`, read its JSON. Lead with 2-3 highest-value next commands with one-line reasons, then the full menu. Never auto-run a command. If `scan.targets` is non-empty, also run `node ./scripts/detect.mjs --json <targets>` for real signals.
2. **First word matches a command**: load its reference and follow instructions. Everything after the command name is the target.
3. **First word doesn't match but intent maps to one command**: load that reference and proceed. If ambiguous, ask once.
4. **No clear match**: general design invocation. Apply setup steps, General rules, and register reference.

## Pin / Unpin

Creates/removes a standalone shortcut so `/<command>` invokes `/impeccable <command>`.

```bash
node ./scripts/pin.mjs <pin|unpin> <command>
```
