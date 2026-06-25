# Taste-Skill — Gemini CLI Bridge

> Loads **before** any UI/UX work. Mirrors `taste-router.md` so Gemini CLI sessions in this repo get the same anti-slop rules as Claude Code.

---

## 🎚️ Why this file exists

This repo integrates the full [taste-skill](https://github.com/leonxlnx/taste-skill) suite (13 skills, 3-dial system, brief-inference, pre-flight checklist). Gemini CLI does not read `.claude/rules/`, so this file is the cross-CLI bridge — it carries the same enforceable rules in a format Gemini CLI picks up via `GEMINI.md`.

---

## 📚 13 Skills (NL-routed — no slash commands needed)

Skills auto-activate from prompt matches. Variants:

| Prompt signal | Skill to load |
|---|---|
| New landing page / portfolio / marketing site | `taste-skill` (v2, **default**) |
| Premium / Apple-y / luxury / Awwwards | `soft-skill` |
| Minimalist / clean / editorial / Notion-style | `minimalist-skill` |
| Brutalist / Swiss / data-dense / HUD | `brutalist-skill` |
| Redesign / audit this UI / looks generic | `redesign-skill` |
| Output is truncating / `// ...` placeholders | `output-skill` (always co-load) |
| Target is GPT-4 / GPT-5 / Codex | `gpt-tasteskill` |
| Pin to v1 (legacy) | `taste-skill-v1` |
| Image-to-code / match a reference | `image-to-code-skill` |
| Google Stitch DESIGN.md | `stitch-skill` |
| Web section image comps | `imagegen-frontend-web` |
| iOS / Android screen concepts | `imagegen-frontend-mobile` |
| Brand kit / identity board | `brandkit` |

Source: `.claude/skills/<name>/SKILL.md`

---

## 🎚️ 3-Dial System (declare before any code)

```
DESIGN_VARIANCE:  8   (1 = symmetric,         10 = artsy chaos)
MOTION_INTENSITY: 6   (1 = static,            10 = cinematic / physics)
VISUAL_DENSITY:   4   (1 = gallery airy,      10 = cockpit packed)
```

Override per brief:
- Minimalist / clean / editorial → VARIANCE 5-6, MOTION 3-4, DENSITY 2-3
- Premium consumer / Apple-y → VARIANCE 7-8, MOTION 5-7, DENSITY 3-4
- Landing / marketing (default) → VARIANCE 7-9, MOTION 6-8, DENSITY 3-5
- Data dashboard / IDE-style → VARIANCE 4-5, MOTION 2-4, DENSITY 7-9
- Trust-first / public-sector → VARIANCE 3-4, MOTION 2-3, DENSITY 4-5

---

## 📝 Brief Inference (MANDATORY — one line before code)

```
Reading this as: <page kind> for <audience>, with a <vibe> language, leaning toward <design system>.
```

---

## ✅ Pre-Flight Checklist (18 items, before declaring done)

```
[ ] Brief read declared on its own line
[ ] Dials stated (VARIANCE / MOTION / DENSITY)
[ ] taste-skill variant identified
[ ] No banned fonts (Inter, Roboto, Arial, Open Sans, system-ui)
[ ] No banned icons (Lucide, Heroicons solid, FontAwesome) → use Phosphor Light, Remix Line
[ ] No purple/indigo gradient backgrounds
[ ] No "3-equal-icon-cards" feature grid
[ ] No `linear-gradient()` on buttons
[ ] Body text not pure #000000 (use off-black #111 or charcoal)
[ ] Headlines letter-spacing -0.02em to -0.04em
[ ] Layout symmetric OR explicitly asymmetric with intent
[ ] No emoji as icons
[ ] No "Welcome to [App Name]" headings
[ ] All CTAs are full sentences / specific verbs
[ ] output-skill enforced: no "// ..." placeholders
[ ] All interactive elements Tab + Enter/Space accessible
[ ] Dark mode token set declared
[ ] Mobile collapse strategy explicit
```

Gate: 3+ fail → regenerate. 1-2 fail → fix inline.

---

## 🚫 Anti-Slop (the 5 pillars)

1. **No generic UI** — never default SaaS templates. Strong typographic hierarchy, alignment care.
2. **Premium whitespace** — `clamp()` over rigid padding. Let elements breathe.
3. **Cinematic motion** — never linear easing. Spring physics (`stiffness: 100, damping: 20`).
4. **Complete implementation** — no `// TODO: add actual code here`. Ship the full working file.
5. **Contextual awareness** — read the localized `SKILL.md` for deep style configs.

---

## 📁 Layout

| Path | Purpose |
|---|---|
| `.claude/skills/<variant>/SKILL.md` | Skill recipes (13 files) |
| `.claude/rules/taste-router.md` | Claude Code variant picker + dials |
| `.claude/rules/ui-ux-excellence.md` | Forbidden-pattern detector |
| `.github/copilot-instructions.md` | GitHub Copilot bridge |
| `AGENTS.md` | Cursor / Windsurf / Codex / Aider / Continue bridge |
| `GEMINI.md` | **This file** — Gemini CLI bridge |
| `skill.sh` | `source ./skill.sh <name>` → prints path to SKILL.md |

---

## 🔄 Rollback

```bash
mv .claude/rules/taste-router.md{,.disabled}
mv GEMINI.md{,.disabled}
mv .github/copilot-instructions.md{,.disabled}
```

---

## 🎨 Impeccable — companion vocabulary skill

The repo also ships [impeccable](https://github.com/pbakaus/impeccable) — a separate, vocabulary-first design skill from pbakaus. It is auto-discovered from `.gemini/skills/impeccable/SKILL.md` (already installed).

### When to use impeccable vs taste-skill

| Signal | Load | Why |
|---|---|---|
| `/impeccable <cmd>` or mentions of named commands (`audit`, `polish`, `critique`, `distill`, `harden`, `animate`, `bolder`, `quieter`, `typeset`, `layout`, `colorize`, `adapt`, `onboard`, `overdrive`, `delight`, `optimize`, `clarify`, `extract`, `document`, `init`, `shape`, `craft`, `live`) | **impeccable** | 23-command vocabulary |
| Brand-vs-product register, "anti-pattern rules", "design vocabulary" | **impeccable** | vocabulary-first design skill |
| Specific shape (Soft, Minimalist, Brutalist) or 3-dial spec (VARIANCE / MOTION / DENSITY) | **taste-skill** | dial-system + shape picker |
| "redesign" / "audit this UI" | **taste-skill `redesign-skill`** (preferred) | taste-skill's audit is more aggressive |

Both skills ban the same LLM tells. Cross-check both pre-flight checklists (taste-router's 18 items + impeccable's 27-rule detector via `npx impeccable detect`).

### How to invoke impeccable in Gemini CLI

```bash
# In a Gemini session:
/skills list                                  # verify impeccable is loaded
# Then either:
# 1. The /impeccable slash command (if user-invocable skills are exposed)
# 2. Read .gemini/skills/impeccable/SKILL.md directly and follow its router table
```

The canonical install is in `.claude/skills/impeccable/`; `.gemini/skills/impeccable/` is a byte-identical copy so Gemini CLI auto-discovers it.

### Impeccable rollback

```bash
rm -rf .claude/skills/impeccable/ .gemini/skills/impeccable/ .cursor/skills/impeccable/ \
       .opencode/skills/impeccable/ .pi/skills/impeccable/ .agents/skills/impeccable/ \
       .github/skills/impeccable/ .kiro/skills/impeccable/ .trae/skills/impeccable/ \
       .trae-cn/skills/impeccable/ .rovodev/skills/impeccable/ .qoder/skills/impeccable/
```
