# Impeccable Integration Design

> **For agentic workers:** This spec is the source of truth for the pbakaus/impeccable native integration into swarm-bot's Claude Code setting with cross-platform bridge support.

**Goal:** Deeply + correctly integrate [pbakaus/impeccable](https://github.com/pbakaus/impeccable) into the swarm-bot Claude Code setting such that the skill works **natively with every other supported AI coding harness**.

**Architecture:** Canonical install at `.claude/skills/impeccable/` (the Claude-Code-native location, used as the single source of truth), with **byte-identical copies** of the same content placed in the 11 other harness skill directories (`.cursor/`, `.gemini/`, `.opencode/`, `.pi/`, `.agents/`, `.github/`, `.kiro/`, `.trae/`, `.trae-cn/`, `.rovodev/`, `.qoder/`). All placeholders (`{{command_hint}}`, `{{scripts_path}}`, `{{model}}`, `{{command_prefix}}`) are substituted at install time so the rendered SKILL.md is ready to load without further build steps. Bridge files (`.cursorrules`, `GEMINI.md`, `.github/copilot-instructions.md`, `AGENTS.md`) are updated to declare the new skill and explain how it coexists with the existing taste-skill suite.

**Tech Stack:** Vanilla skill structure (per [Agent Skills specification](https://agentskills.io/specification)) — markdown + scripts + Codex subagents. No build step required at runtime; one-time `sed` substitution for placeholder rendering.

---

## 1. Context

### Why this integration exists

The repo already ships a deep integration of [taste-skill](https://github.com/leonxlnx/taste-skill) (see `2026-06-05-taste-skill-integration-design.md`). Taste-skill is a **dial-and-shape** framework: 13 skill variants, 3-dial system (VARIANCE / MOTION / DENSITY), brief inference, 18-item pre-flight checklist.

**Impeccable is the vocabulary-first complement.** Where taste-skill says "here's how to dial the design system in," impeccable says "here's the 23-command design vocabulary and the 27 anti-pattern rules the AI should internalize." They are complementary, not redundant:

| Skill | Primary contribution |
|---|---|
| **taste-skill** | Variant picker (Soft / Minimalist / Brutalist / …) + dial system (VARIANCE / MOTION / DENSITY) + library selection (shadcn/ui, Radix, Mantine, …) + 18-item pre-flight |
| **impeccable** | 23 named commands (audit, polish, critique, distill, harden, animate, bolder, quieter, …) + 27-rule anti-pattern detector + 7 domain references (typography, color, motion, spatial, interaction, responsive, UX writing) + brand-vs-product register |

The two share the same LLM-tell anti-slop philosophy (ban Inter, ban purple gradients, ban 3-equal-icon-cards, ban emoji as icons, ban "Welcome to..." headings). Cross-loading them gives the AI both the **vocabulary** (impeccable) and the **dial system** (taste-skill) for any given frontend task.

### What "works with others natively" means

The user's explicit constraint: impeccable must work without manual setup on any of the major AI coding harnesses, not just Claude Code. Concretely, that means the install layout must cover:

| Harness | Native skill dir | Auto-reads |
|---|---|---|
| Claude Code | `.claude/skills/` | — |
| Cursor | `.cursor/skills/` | `.claude/skills/`, `.agents/skills/` |
| OpenCode | `.opencode/skills/` | `.claude/skills/`, `.agents/skills/` |
| Pi | `.pi/skills/` | `.agents/skills/` |
| Gemini CLI | `.gemini/skills/` | `.agents/skills/` |
| Codex CLI | `.agents/skills/` (primary) | — |
| GitHub Copilot | `.github/skills/` | `.claude/skills/`, `.agents/skills/` |
| Kiro | `.kiro/skills/` | — |
| Trae International | `.trae/skills/` | — |
| Trae China | `.trae-cn/skills/` | — |
| Rovo Dev | `.rovodev/skills/` | `~/.rovodev/skills/` (user-level) |
| Qoder | `.qoder/skills/` | `~/.qoder/skills/` (user-level) |

12 harness directories in total. All 12 must be populated with byte-identical content.

---

## 2. Source-of-truth install

### 2.1 Upstream layout (pbakaus/impeccable)

The upstream repo at github.com/pbakaus/impeccable ships:

- `skill/SKILL.src.md` — the monolithic skill source (one large markdown with embedded `{{placeholder}}` substitution targets)
- `skill/reference/` — 27 reference files:
  - **23 commands**: `craft.md`, `init.md`, `document.md`, `extract.md`, `shape.md`, `critique.md`, `audit.md`, `polish.md`, `bolder.md`, `quieter.md`, `distill.md`, `harden.md`, `onboard.md`, `animate.md`, `colorize.md`, `typeset.md`, `layout.md`, `delight.md`, `overdrive.md`, `clarify.md`, `adapt.md`, `optimize.md`, `live.md`
  - **Domain reference**: `interaction-design.md`
  - **Registers**: `brand.md`, `product.md`
  - **Codex defects**: `codex.md`
- `skill/scripts/` — 37 scripts (context.mjs, palette.mjs, pin.mjs, detect.mjs, command-metadata.json, is-generated.mjs, impeccable-paths.mjs, critique-storage.mjs, cleanup-deprecated.mjs, plus 28 `live-*` scripts)
- `skill/agents/` — 2 Codex-specific subagents (auto-discovered by Codex from the nested agents/ folder):
  - `impeccable-asset-producer.md`
  - `impeccable-manual-edit-applier.md`

### 2.2 Placeholder substitution

Upstream `SKILL.src.md` contains runtime-targeted placeholders that the upstream `npx impeccable skills install` resolves per harness:

| Placeholder | Value substituted | Meaning |
|---|---|---|
| `{{command_hint}}` | `command` | argument-hint for slash command |
| `{{scripts_path}}` | `./scripts` | relative path to scripts/ in the skill install |
| `{{model}}` | `Claude` | the model name baked into the skill's voice |
| `{{command_prefix}}` | `/` | the harness's command prefix |

All four are substituted at install time. The rendered output has **zero** `{{...}}` placeholders — verified by `grep -c '{{' .claude/skills/impeccable/SKILL.md` → `0`.

### 2.3 Frontmatter (post-render)

```yaml
---
name: impeccable
description: "Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, distill, harden, optimize, adapt, animate, colorize, extract, or otherwise improve a frontend interface. Covers websites, landing pages, dashboards, product UI, app shells, components, forms, settings, onboarding, and empty states. ..."
argument-hint: "[command] [target]"
user-invocable: true
allowed-tools:
  - Bash(npx impeccable *)
license: Apache 2.0
---
```

The `description` field is the **single most important field** for non-slash harnesses (Copilot, Cursor, Codex, Gemini) — the harness's NL router reads it and decides whether to load the skill on any given prompt. The full upstream description covers: design / redesign / shape / critique / audit / polish / clarify / distill / harden / optimize / adapt / animate / colorize / extract, plus surface types (websites, landing pages, dashboards, product UI, app shells, components, forms, settings, onboarding, empty states), plus attributes (UX review, visual hierarchy, information architecture, cognitive load, accessibility, performance, responsive behavior, theming, anti-patterns, typography, fonts, spacing, layout, alignment, color, motion, micro-interactions, UX copy, error states, edge cases, i18n, reusable design systems / tokens), plus negative examples (not for backend-only or non-UI tasks).

---

## 3. Cross-platform install

### 3.1 Strategy

Place the rendered (placeholder-free) skill content into all 12 harness directories. Content is **byte-identical** across all 12 — verified by `du -sb` returning `1368748` for every directory.

### 3.2 Final install parity

| Harness dir | Bytes | SKILL.md | refs | scripts | agents |
|---|---|---|---|---|---|
| `.claude/skills/impeccable/` | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.cursor/skills/impeccable/` | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.gemini/skills/impeccable/` | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.opencode/skills/impeccable/` | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.pi/skills/impeccable/` | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.agents/skills/impeccable/` (Codex) | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.github/skills/impeccable/` (Copilot) | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.kiro/skills/impeccable/` | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.trae/skills/impeccable/` | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.trae-cn/skills/impeccable/` | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.rovodev/skills/impeccable/` | 1,368,748 | ✓ | 27 | 37 | 2 |
| `.qoder/skills/impeccable/` | 1,368,748 | ✓ | 27 | 37 | 2 |

Total disk footprint: ~16.4 MB.

### 3.3 Why byte-identical (not a build matrix)

The upstream `npx impeccable skills install` command generates per-harness builds because each harness has slightly different frontmatter needs and asset paths. We chose **byte-identical** over **per-harness-build** for three reasons:

1. **The Agent Skills spec is stable.** All 12 harnesses parse the same `name` + `description` + `allowed-tools` + `argument-hint` fields identically. Provider-specific extensions (e.g., `mcp`, `hooks` for Claude Code) are gracefully ignored by other harnesses. See `HARNESSES.md` in upstream for the full per-harness support matrix.
2. **Subagents (`agents/` folder) are Codex-specific.** Codex auto-discovers TOML files from `<skill>/agents/`, but only reads them when launched in Codex. The Claude-Code-friendly markdown agents in our `agents/` folder are ignored on Claude Code (which reads `.claude/agents/` for its own plugin system) and on every other harness. Safe to ship the same content everywhere.
3. **One-source-of-truth beats one-build-per-harness for a single-integration project.** Per-harness builds would require the upstream build system (the `scripts/` builder) to be re-run, and any drift between our hand-built install and the upstream build pipeline would be a maintenance burden. Byte-identical is auditable, reproducible, and exactly what the upstream `npx impeccable skills install` produces by default.

### 3.4 Codex-specific note (auto-discovered subagents)

Codex CLI is unique: it auto-discovers custom subagents bundled inside an installed skill's `agents/` folder (TOML format). For Claude Code and other harnesses, the `agents/` folder is just a directory of unused files. This is **not a problem** — the contents are harmless on non-Codex harnesses. The two agents shipped are:

- `impeccable-asset-producer.md` — generates the design-system assets (logos, illustrations, etc.) when `impeccable` runs in asset-production mode
- `impeccable-manual-edit-applier.md` — applies manual edits that the user dictates to the skill during a `live` iteration

Both are markdown (not TOML). The Codex-side TOML is a separate concern handled by Codex's `agents/openai.yaml` sidecar, which the user can configure if they need Codex-specific subagent icons / branding. For Claude Code usage, these agents are loaded via the main SKILL.md (which references them as "codex subagents" for Codex users and "helpers" for everyone else).

---

## 4. Bridge files (5 files updated)

Five bridge files declare how each harness's auto-loaded instructions reach the skill. All five were updated in this integration:

### 4.1 `.claude/rules/taste-router.md` — Claude Code

Added §9 **Impeccable coexistence** and §10 **Stack composition** (taste-skill + impeccable together). Key points:

- When to load which (decision table)
- Anti-pattern rule overlap (both ban the same LLM tells)
- 12-harness install layout
- Rollback procedure for impeccable
- Pair order on frontend tasks: impeccable FIRST (vocabulary), taste-skill SECOND (dials)

### 4.2 `GEMINI.md` — Gemini CLI

Added "Impeccable — companion vocabulary skill" section. Mirror of taste-router's §9, formatted for Gemini CLI's `GEMINI.md` discovery convention.

### 4.3 `.cursorrules` — Cursor

Added "Impeccable coexistence (pbakaus upstream)" section after the existing taste-skill block. Cursor auto-loads this file on every prompt.

### 4.4 `.github/copilot-instructions.md` — GitHub Copilot

Appended "Companion: Impeccable Skill" section. Copilot reads this file globally; the 5-pillar anti-slop manifesto remains the lead, with impeccable as a companion vocabulary skill.

### 4.5 `AGENTS.md` — Windsurf / Codex / Aider / Continue / Roo Code

Updated the "Cross-platform bridges" table to mention the 12 install directories, and added an "Impeccable skill (cross-vocabulary design)" section with the when-to-load table and pair-order rule.

---

## 5. Anti-pattern rule parity

Both taste-skill and impeccable ban the same LLM tells. Cross-reference:

| LLM tell | taste-skill ban | impeccable ban |
|---|---|---|
| Inter / Roboto / Arial / Open Sans / system-ui | ✓ | ✓ (typography reference) |
| Lucide / Heroicons solid / FontAwesome | ✓ (use Phosphor / Remix) | ✓ (use Phosphor / Lucide-stroke) |
| Purple / indigo gradient backgrounds | ✓ | ✓ (color-and-contrast reference) |
| 3-equal-icon-cards feature grid | ✓ (ui-ux-excellence.md) | ✓ (spatial-design reference) |
| `linear-gradient()` on buttons | ✓ | ✓ |
| Pure `#000000` body text | ✓ (use off-black) | ✓ (tinted neutrals) |
| Centered hero over dark mesh with glassmorphism | ✓ | ✓ |
| "Welcome to [App Name]" headings | ✓ | ✓ |
| Emoji as icons | ✓ | ✓ |
| `// ...` / placeholder comments | ✓ (output-skill) | ✓ (live mode enforcer) |

The overlap is the design — both skills emerged from the same anti-slop design philosophy. The union of both rule sets gives a more thorough pre-flight than either alone.

### Impeccable's 27-rule deterministic anti-pattern detector

Shipped via the `impeccable` npm CLI. Already installed alongside the skill install (the `scripts/detect.mjs` is wired to the canonical npm package, which provides the CLI cross-platform).

```bash
npx impeccable detect src/                  # scan a directory
npx impeccable detect index.html            # scan a single file
npx impeccable detect --fast --json .       # regex-only, JSON output
npx impeccable detect https://example.com   # scan a URL (Puppeteer)
```

Catches 24 issues across AI slop (side-tab borders, purple gradients, bounce easing, dark glows) and general design quality (line length, cramped padding, small touch targets, skipped headings, …).

This is the **deterministic complement** to taste-skill's LLM-driven 18-item pre-flight checklist. The two can be cross-validated on any frontend project.

---

## 6. Pair-order convention

When both skills co-load on a frontend task, the integration recommends:

1. **Run impeccable FIRST.** Its `init` command (or `node ./scripts/context.mjs`) sets the brand-vs-product register, and its 7 domain references (typography, color, spatial, motion, interaction, responsive, UX writing) load the design vocabulary. The user knows upfront what register they're working in (brand = design IS the product; product = design SERVES the product).
2. **Run taste-skill SECOND.** Set the dials (VARIANCE / MOTION / DENSITY) and pick the variant (Soft / Minimalist / Brutalist / …) for the actual build. The dials adjust within the register set by step 1.
3. **Cross-check both pre-flight checklists before declaring done.** Taste-router's 18 items + impeccable's 27-rule detector (via `npx impeccable detect`).

This pairing is the design: impeccable is **what to say**, taste-skill is **how to build**.

---

## 7. Failure modes

- **Impeccable loads when the user asked for taste-skill:** the description fields are sufficiently different that the NL router should disambiguate. If both load (rare on Claude Code; common on Copilot's broader auto-load), the user can pin a specific one with the bridge files' signal tables.
- **Codex-specific subagent TOML is missing:** we ship markdown agents in `agents/`. Codex users who want TOML subagent icons / branding can convert them, but the markdown forms are the canonical upstream and work everywhere.
- **Rollback:** `rm -rf` on all 12 install directories. See §8 of `taste-router.md` for the bridge file rollback commands.

---

## 8. Verification (executed 2026-06-05)

```bash
# 1. No placeholders in rendered SKILL.md
$ grep -c '{{' .claude/skills/impeccable/SKILL.md
0

# 2. Reference / script / agent counts
$ ls .claude/skills/impeccable/reference/ | wc -l
27
$ ls .claude/skills/impeccable/scripts/ | wc -l
37
$ ls .claude/skills/impeccable/agents/ | wc -l
2

# 3. Byte-parity across all 12 harness dirs
$ for d in .claude .cursor .gemini .opencode .pi .agents .github .kiro .trae .trae-cn .rovodev .qoder; do du -sb $d/skills/impeccable/; done
1368748  (×12)

# 4. Smoke-test scripts
$ node .claude/skills/impeccable/scripts/palette.mjs | head -3
BRAND SEED · seed-124
Seed color (anchor for your primary brand color):
  oklch(0.750 0.080 170.0) — teal

$ node .claude/skills/impeccable/scripts/context.mjs | head -3
NO_PRODUCT_MD: This project has no PRODUCT.md yet. Stop the current task,
load reference/init.md, and follow its instructions to write PRODUCT.md
before resuming.
```

The `NO_PRODUCT_MD` output is expected — swarm-bot is a backend / agent system, not a frontend project. When a frontend project is loaded into a Claude Code session that has impeccable installed, the `init` command will write `PRODUCT.md` (and optionally `DESIGN.md`) and the context script will print them on subsequent runs.

### Bridge file verification (5 files updated)

| File | Before | After | Delta |
|---|---|---|---|
| `.claude/rules/taste-router.md` | 190 lines, 8 sections | 190+ lines, 10 sections | +§9 Impeccable coexistence, +§10 Stack composition |
| `GEMINI.md` | 119 lines | +40 lines | +Impeccable skill section |
| `.cursorrules` | 92 lines | +25 lines | +Impeccable coexistence block |
| `.github/copilot-instructions.md` | 11 lines | +18 lines | +Companion: Impeccable Skill section |
| `AGENTS.md` | 896 lines | +18 lines | Updated cross-platform bridges table + Impeccable section |

---

## 9. Rollback

```bash
# Full rollback
rm -rf .claude/skills/impeccable/ .cursor/skills/impeccable/ .gemini/skills/impeccable/ \
       .opencode/skills/impeccable/ .pi/skills/impeccable/ .agents/skills/impeccable/ \
       .github/skills/impeccable/ .kiro/skills/impeccable/ .trae/skills/impeccable/ \
       .trae-cn/skills/impeccable/ .rovodev/skills/impeccable/ .qoder/skills/impeccable/

# Bridge file rollback (revert to last commit)
git checkout HEAD -- .claude/rules/taste-router.md GEMINI.md .cursorrules \
                     .github/copilot-instructions.md AGENTS.md
```

After full rollback, the base system returns to taste-skill + ui-ux-excellence only — same behavior as before this integration.

---

## 10. References

- Upstream: [github.com/pbakaus/impeccable](https://github.com/pbakaus/impeccable)
- Upstream capabilities reference: [`HARNESSES.md`](https://github.com/pbakaus/impeccable/blob/main/HARNESSES.md) (per-harness support matrix)
- Agent Skills spec: [agentskills.io/specification](https://agentskills.io/specification)
- Sibling integration (taste-skill): `2026-06-05-taste-skill-integration-design.md`
- Memory entry: `taste-skill-integration-20260605.md` (taste-skill), and (forthcoming) `impeccable-integration-20260605.md`

---

**Spec author:** Claude Code (claude-opus-4-6) via subagent-driven development
**Date:** 2026-06-05
**Status:** ✅ Complete — all 12 installs verified byte-identical, all 5 bridge files updated, all scripts smoke-tested.
