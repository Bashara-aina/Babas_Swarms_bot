# Design Rules Reference

Load this file when you need the full detailed design guidance. The SKILL.md contains a condensed summary.

## Color

- Verify contrast: body text >= 4.5:1 against background; large text (>=18px or bold >=14px) >= 3:1. Placeholder text needs 4.5:1, not muted gray.
- Gray text on colored background looks washed out. Use a darker shade of the background's own hue, or a transparency of the text color.
- Use OKLCH color space.
- **The cream/sand/beige body bg is the saturated AI default of 2026.** Warm-neutral band (OKLCH L 0.84-0.97, C < 0.06, hue 40-100) reads as cream regardless of token name. If the brief is "warm", don't default to warm-tinted near-white bg. Pick: (a) saturated brand color as body, (b) true off-white at chroma 0, (c) darker mid-tone tinted toward brand's own hue.
- Tinted neutrals: add 0.005-0.015 chroma toward brand's hue. Don't default-tint toward warm/cool.
- Pick theme by writing one sentence of physical scene (who, where, under what light, in what mood). If it doesn't force dark vs light, add detail until it does.
- **Color strategy** (4 levels): Restrained (tinted neutrals + one accent <=10%), Committed (one saturated color 30-60% of surface), Full palette (3-4 named roles), Drenched (surface IS the color).

## Typography

- Body line length: 65-75ch.
- Scale ratio >= 1.25 between steps.
- Cap font-family count at 3 (display + body + optional mono).
- Pair on contrast axis (serif + sans, geometric + humanist) or use one family in multiple weights.
- No all-caps body copy. Uppercase only for short labels (<=4 words), section eyebrows, badges.
- Hero/display heading ceiling: clamp() max <= 6rem (~96px).
- Display heading letter-spacing floor: >= -0.04em.
- Use `text-wrap: balance` on h1-h3; `text-wrap: pretty` on long prose.

Two hard ceilings: Hero clamp() max <= 6rem (not 8-11rem). Display letter-spacing >= -0.04em (not -0.05 to -0.085).

## Layout

- Vary spacing for rhythm.
- Cards are the lazy answer. Use only when truly the best affordance. Nested cards are always wrong.
- Flexbox for 1D, Grid for 2D. Don't default to Grid when `flex-wrap` suffices.
- For responsive grids without breakpoints: `repeat(auto-fit, minmax(280px, 1fr))`.
- Build a semantic z-index scale (dropdown -> sticky -> modal-backdrop -> modal -> toast -> tooltip). Never 999/9999.

## Motion

- Intentional, not an afterthought. Don't animate CSS layout properties.
- Ease out with exponential curves (quart/quint/expo). No bounce, no elastic.
- Use libraries for advanced needs (motion, gsap, anime.js, lenis).
- Reduced motion: every animation needs `@media (prefers-reduced-motion: reduce)` alternative.
- Staggering within one list is legitimate. Suppressing all motion to avoid "the reflex" is never a reason to ship without motion.
- Reveal: enhance already-visible defaults. Don't gate content visibility on class-triggered transitions.
- Premium materials: blur, backdrop-filter, clip-path, mask, shadow/glow are part of the palette.

## Interaction

- Dropdowns with `position: absolute` inside `overflow: hidden/auto` will clip. Use `<dialog>`, popover API, `position: fixed`, or a portal.
- **Never animate `<img>` on hover** — no `transform` on `:hover` of an image, no Tailwind `.group-hover:scale`/`.group-hover:rotate` that animate child images. This is the single most common AI motion tell. Animate card background, border, or shadow instead.

## Copy

- Every word earns its place. No restated headings, no intros that repeat the title.
- No em dashes. Use commas, colons, semicolons, periods, or parentheses.
- No aphoristic-cadence body copy — don't default to "serious statement, then punchy short negation."
- No marketing buzzwords (streamline, empower, supercharge, leverage, etc.). Pick specific nouns and verbs.
- Button labels: verb + object. "Save changes" beats "OK".
- Link text needs standalone meaning. "View pricing plans" beats "Click here".
