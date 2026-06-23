---
name: taste-router
description: Routes UI/UX work through taste-skill — applies dials (VARIANCE/MOTION/DENSITY), brief-inference protocol, and pre-flight checklist to every frontend output. Layered on top of ui-ux-excellence.md; this rule decides WHICH taste-skill variant each design sub-discipline loads, not what the variants contain.
type: rule
applies_to: design-dept, frontend-dev, branding, motion, redesign
---

# 🎚️ TASTE-SKILL ROUTER — Dial Setter + Pre-Flight Checklist

> Pairs with `ui-ux-excellence.md` (forbidden-pattern detector + component quality). This file owns the dial system, brief inference protocol, and pre-flight checklist. No variant picker needed — `impeccable` (`.claude/skills/impeccable/`) is the loaded design skill.

---

## §0 — WHY THIS RULE EXISTS

Without routing, every agent falls back to LLM defaults (Inter + slate-900 + 3-column icon cards + purple gradient). This rule:

1. **Sets** the dials based on brief inference (VARIANCE 1-10 / MOTION 1-10 / DENSITY 1-10)
2. **Forces** the brief-inference line before any code
3. **Forces** the pre-flight checklist before any output

The referenced taste-skill variants (soft, minimalist, brutalist, redesign, etc.) do not exist as installed skills. Use `impeccable` (`.claude/skills/impeccable/`) as the primary design vocabulary and execution skill.

---

## §2 — DIAL SETTING (VARIANCE / MOTION / DENSITY)

After picking the variant, set three numeric dials. Every layout, motion, and density decision is gated by these.

```
DESIGN_VARIANCE:  8   (1 = perfect symmetry, 10 = artsy chaos)
MOTION_INTENSITY: 6   (1 = static,           10 = cinematic / physics)
VISUAL_DENSITY:   4   (1 = art gallery airy, 10 = cockpit data-packed)
```

**Baseline: 8 / 6 / 4.** Override per brief:

| Brief signal | VARIANCE | MOTION | DENSITY |
|---|---|---|---|
| minimalist / clean / calm / editorial / Linear-style | 5-6 | 3-4 | 2-3 |
| premium consumer / Apple-y / luxury / brand | 7-8 | 5-7 | 3-4 |
| playful / wild / Dribbble / Awwwards / experimental / agency | 9-10 | 8-10 | 3-4 |
| landing page / portfolio / marketing site (default) | 7-9 | 6-8 | 3-5 |
| trust-first / public-sector / regulated / accessibility-critical | 3-4 | 2-3 | 4-5 |
| data dashboard / engineering tool / IDE-style | 4-5 | 2-4 | 7-9 |

**Dial defaults per design sub-agent** (lock these unless brief overrides):

| Agent | VARIANCE | MOTION | DENSITY | Notes |
|---|---|---|---|---|
| `taste_frontend_architect` (orchestrator) | from brief | from brief | from brief | reads the brief, declares dials |
| `ux_designer` | 6 | 4 | 3 | calm, restrained, editorial |
| `graphic_designer` | 7 | 5 | 4 | visual-first, brand-faithful |
| `branding_strategist` | 6 | 4 | 3 | voice + identity, low motion |
| `motion_artist` | 8 | 9 | 4 | max motion, less density |
| `spatial_designer` | 8 | 7 | 5 | 3D, depth, more density |
| `wireframe_specialist` | 4 | 2 | 3 | lo-fi, static, sparse |
| `color_expert` | 5 | 3 | 4 | palette discipline |
| `accessibility_auditor` | 4 | 3 | 5 | WCAG-first, predictable motion |
| `prototype_builder` | 7 | 7 | 4 | interactive, demonstrate motion |
| `user_flow_mapper` | 4 | 2 | 4 | diagrams, static, denser |

**Hard rule:** `wireframe_specialist` / `user_flow_mapper` / `accessibility_auditor` NEVER use high motion. They intentionally bias low VARIANCE + low MOTION + medium DENSITY. Their outputs look like Figma/Linear, not Apple-keynote.

---

## §3 — BRIEF INFERENCE (MANDATORY before any code)

Before any frontend code or design recommendation, output exactly ONE line:

```
Reading this as: <page kind> for <audience>, with a <vibe> language, leaning toward <design system>.
```

Examples:
- *"Reading this as: B2B SaaS landing for technical buyers, with a Linear-style minimalist language, leaning toward Tailwind utilities + Geist + restrained motion."*
- *"Reading this as: solo designer portfolio for hiring managers, with an editorial / kinetic-type language, leaning toward native CSS + scroll-driven animation + custom typography."*
- *"Reading this as: redesign of a public-sector service site, with a trust-first language, leaning toward GOV.UK Frontend or USWDS."*

**Anti-default discipline:** Do NOT default to AI-purple gradients, centered hero over dark mesh, three equal feature cards, generic glassmorphism, infinite-loop micro-animations, Inter + slate-900. These are the LLM defaults. Reach past them deliberately based on the design read.

**If the brief is ambiguous, ask ONE clarifying question** (never a multi-question dump), and only when the design read genuinely diverges. Example: *"Should this feel closer to Linear-clean or Awwwards-experimental?"* If you can confidently infer, do not ask.

---

## §4 — PRE-FLIGHT CHECKLIST (before declaring "done")

Before outputting frontend code, run this checklist. If any item fails, fix it inline.

```
[ ] Brief read declared on its own line (format above)
[ ] Dials stated (VARIANCE / MOTION / DENSITY)
[ ] taste-skill variant identified (or "default v2")
[ ] No banned fonts (Inter, Roboto, Arial, Open Sans, system-ui) unless accessibility constraint
[ ] No banned icons (Lucide, Heroicons solid, FontAwesome) — use Phosphor Light, Remix Line, or hand-drawn
[ ] No purple/indigo gradient backgrounds
[ ] No "3-equal-icon-cards" feature grid (the AI slop tell)
[ ] No `linear-gradient()` on buttons — solid accent only
[ ] Body text not pure #000000 — use off-black (#111 or charcoal)
[ ] Headlines have `letter-spacing: -0.02em` to `-0.04em` and tight line-height
[ ] Layout either fully symmetric OR explicitly asymmetric with intent — not "default centered"
[ ] No emoji as icons
[ ] No "Welcome to [App Name]" headings
[ ] All CTAs are full sentences or specific verbs (never "Click here")
[ ] output-skill enforced: no "// ..." or "rest follows the same pattern" in code
[ ] All interactive elements are Tab + Enter/Space accessible
[ ] Dark mode token set declared (even if light-only shipped)
[ ] Mobile collapse strategy explicit (`w-full`, `px-4`, `min-h-[100dvh]`)
```

**Gate:** If 3+ items fail, regenerate. If 1-2 items fail, fix inline. Document the check in the response so the user sees the work.

---

## §5 — INTEGRATION WITH ui-ux-excellence.md

This rule does NOT replace `ui-ux-excellence.md`. It runs ON TOP:

- **taste-router.md** (this file) — picks variant, sets dials, enforces brief-inference + pre-flight
- **ui-ux-excellence.md** — owns the forbidden-pattern detector (purple gradients, 3-col icon cards, "Welcome to...") and component-quality rules (shadows, buttons, forms, empty states)
- **taste-skill SKILL.md** — the actual recipes (font pairings, motion physics, bento grid math, GSAP snippets, color tokens)
- **output-skill** — no placeholder output, full deliverables

When in doubt: taste-router decides WHICH. ui-ux-excellence decides WHAT to avoid. taste-skill decides HOW to build it. output-skill ensures it ships complete.

---

## §7 — FAILURE MODES (anti-patterns in taste-skill usage itself)

- **Cargo-culted brutalism:** Applying brutalist-skill to a wedding-planning site. Match the variant to the brief.
- **Decorative motion:** motion_artist cranking MOTION=10 on a B2B procurement tool. Dial inference says "trust-first" → MOTION 2-3.
- **3-dial rigid thinking:** Treating VARIANCE=10 as a license for chaos. The dial caps variance, not quality.
- **"I'll just use taste-skill" without reading the brief:** Section §3 brief inference is non-negotiable. Skip it = no taste-skill.
- **Variant thrash:** Loading 4 SKILL.md files at once and mashing them. Pick ONE primary + output-skill. Load a 3rd only if explicitly needed.
- **Skipping pre-flight:** Section §4 gate exists because taste-skill's own audits are easy to forget. Always run the 18-item list before declaring done.

---

## §8 — ROLLBACK

To disable taste-skill routing: rename this file to `.claude/reference/taste-router.md.disabled` and restart.

---

## §9 — IMPECCABLE COEXISTENCE (cross-vocabulary skill)

The repo also ships [impeccable](https://github.com/pbakaus/impeccable) at `.claude/skills/impeccable/` — a separate, **vocabulary-first** design skill from the original pbakaus project. It coexists with taste-skill, they do not conflict.

### When to load which

| Signal | Load | Why |
|---|---|---|
| User says `/impeccable <cmd>` or mentions specific commands (`audit`, `polish`, `critique`, `distill`, `harden`, `animate`, `bolder`, `quieter`, etc.) | **impeccable** | command-router vocabulary |
| User wants shape-then-build with a specific shape (Soft, Minimalist, Brutalist) or a 3-dial spec (VARIANCE / MOTION / DENSITY) | **taste-skill** | dial-system + shape picker |
| User says "redesign" / "audit this UI" / "improve this design" | **taste-skill `redesign-skill`** (preferred) — fallback: `impeccable audit` | taste-skill's audit is more aggressive; impeccable is more conservative |
| User asks for the "23 commands" / "anti-pattern rules" / "design vocabulary" / brand-vs-product register | **impeccable** | upstream vocabulary |
| User wants a single imperative-shaped deliverable on a frontend page | **either works** | both ship a polished pipeline |

### Anti-pattern rule overlap

Both skills ban the same LLM tells (Inter, purple gradients, 3-equal-icon-cards, emoji as icons, etc.). The pre-flight checklist in §4 covers taste-skill's anti-slop rules; impeccable's 27-rule anti-pattern detector runs via the `npx impeccable detect` CLI:

```bash
npx impeccable detect src/                  # scan a directory
npx impeccable detect index.html            # scan a file
npx impeccable detect --fast --json .       # regex-only, JSON output
npx impeccable detect https://example.com   # scan a URL (Puppeteer)
```

This CLI is shipped inside `.claude/skills/impeccable/scripts/` and the canonical install of the `impeccable` npm package provides it cross-platform.

### Skill installation (impeccable — already done)

`impeccable` is installed in **all 12** harness directories so the skill is auto-discovered regardless of which CLI you boot:

```
.claude/skills/impeccable/     ← Claude Code (canonical, with 7-domain refs + 23 commands + 27 refs + 37 scripts)
.cursor/skills/impeccable/     ← Cursor (also reads .claude/skills/ and .agents/skills/)
.gemini/skills/impeccable/     ← Gemini CLI
.opencode/skills/impeccable/   ← OpenCode
.pi/skills/impeccable/         ← Pi
.agents/skills/impeccable/     ← Codex CLI (primary)
.github/skills/impeccable/    ← GitHub Copilot
.kiro/skills/impeccable/       ← Kiro
.trae/skills/impeccable/       ← Trae International
.trae-cn/skills/impeccable/    ← Trae China
.rovodev/skills/impeccable/    ← Rovo Dev
.qoder/skills/impeccable/      ← Qoder
```

Each install is identical: 1 monolithic `SKILL.md` (25KB), 27 reference files (23 commands + `brand.md` + `product.md` + `codex.md` + `interaction-design.md`), 37 scripts, 2 Codex-specific subagents (auto-discovered from `agents/` folder). Total: 1.5MB per install.

### Rollback for impeccable

```bash
rm -rf .claude/skills/impeccable/ .cursor/skills/impeccable/ .gemini/skills/impeccable/ \
       .opencode/skills/impeccable/ .pi/skills/impeccable/ .agents/skills/impeccable/ \
       .github/skills/impeccable/ .kiro/skills/impeccable/ .trae/skills/impeccable/ \
       .trae-cn/skills/impeccable/ .rovodev/skills/impeccable/ .qoder/skills/impeccable/
```

The base system then falls back to taste-skill + ui-ux-excellence only.

---

## §10 — STACK COMPOSITION (taste-skill + impeccable together)

When both skills co-load on the same frontend task:

1. **Run impeccable FIRST** to set vocabulary + brand-vs-product register (it asks the design questions once, then reuses them across commands).
2. **Run taste-skill SECOND** to set dials + variant for the actual build.
3. **Cross-check** both pre-flight checklists before declaring done (taste-router's 18 items + impeccable's 27-rule anti-pattern detector via `npx impeccable detect`).

This pairing is intentional: impeccable is **what to say** (vocabulary, anti-patterns, design register); taste-skill is **how to build** (dials, shapes, motion physics, library selection). The two are complementary, not redundant.
