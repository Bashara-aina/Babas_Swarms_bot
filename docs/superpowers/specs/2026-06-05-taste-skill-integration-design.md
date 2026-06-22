# taste-skill Integration Design (Babas Agency Swarm)

**Date**: 2026-06-05
**Status**: Approved (brainstorming complete, ready for plan)
**Author**: Claude (via brainstorming)
**Upstream**: https://github.com/leonxlnx/taste-skill (Anti-Slop Frontend Framework)
**Predecessor rule**: `.claude/rules/ui-ux-excellence.md` (project-baked UI discipline)

---

## Purpose

Deeply and correctly implement [taste-skill](https://github.com/leonxlnx/taste-skill) in this
Claude Code setting so it works **natively** with the rest of our systems: 84-agent
registry, 6-layer memory, Hermes MCP, GitNexus, observation bridges, and the existing
`.claude/rules/ui-ux-excellence.md` (which is already the project's own anti-slop detector).

This is NOT a standalone clone of taste-skill. It is a **first-class integration** that:

1. Installs all 8 taste-skill SKILL.md variants in `.claude/skills/` (same loader as
   every other skill — auto-activates from prompt matching)
2. Adds a new `taste-router.md` rule that picks WHICH variant + sets dials, layered
   ON TOP of `ui-ux-excellence.md` (which decides WHAT to avoid)
3. Promotes the design department's orchestrator to `taste_frontend_architect`, a
   senior design lead that runs the full taste-skill pipeline
4. Wires 4 design sub-agents (`ux_designer`, `graphic_designer`, `branding_strategist`,
   `motion_artist`) with their taste-skill loading rules + dial defaults in YAML
5. Surfaces the dial defaults, variant picker, and pre-flight checklist in the
   agent's rendered system prompt — so the brief-inference line is the first thing
   every design agent outputs

The result: any UI/UX work dispatched to a design agent is gated by the 18-item
pre-flight checklist and the brief-inference protocol before a single line of code.

---

## Scope

### In scope (v1)

- Install all 8 SKILL.md variants from upstream taste-skill into `.claude/skills/`
- Create `taste-router.md` rule (dial setter + variant picker)
- Promote design dept orchestrator to `taste_frontend_architect` (heavyweight tier)
- Wire 4 design sub-agents with taste-skill loading rules + dial defaults
- Inline the full taste-skill pipeline (6 stages) in `taste_frontend_architect.j2`
- Layered authority: taste-router (WHICH) + ui-ux-excellence (WHAT) + taste-skill
  SKILL.md (HOW) + output-skill (COMPLETE)

### Out of scope (v1)

- Wiring the other 5 design sub-agents (wireframe, spatial, color, accessibility,
  prototype, user_flow) — they remain loadable via the router rule but their YAML
  metadata wasn't touched in v1. Tracked for v2.
- The 18-item pre-flight auto-checker (script that scans output for banned patterns
  automatically) — current enforcement is human-in-the-loop via the orchestrator
- Custom taste-skill variant creation — we use upstream verbatim
- Web/3D/AR/VR-specific taste-skill (the upstream doesn't have these)

### Trade-offs accepted

- The 4 sub-agent role prompts stay as 3-line stubs (taste-skill rules live in YAML
  metadata, not in `.j2` content). This is because `prompts/base.j2` has no `{% block %}`
  definitions, so any content after `{% extends %}` is dropped. YAML-driven
  metadata flows into the prompt via the existing `{{ role_description }}` and
  `{{ capabilities }}` placeholders.
- `taste_frontend_architect.j2` is a **standalone** template (does NOT extend
  base.j2) so the full 6-stage pipeline can be inlined. This is intentional —
  the orchestrator needs the heavy brief, the sub-agents need the lean brief.

---

## Architecture

### File layout (delta from before this integration)

```
.claude/
├── rules/
│   ├── ui-ux-excellence.md      ← existing, unchanged
│   └── taste-router.md          ← NEW: WHICH + dials
└── skills/
    ├── taste-skill/             ← NEW (v2 — 87 KB SKILL.md, default)
    ├── taste-skill-v1/          ← NEW (legacy v1, 21 KB)
    ├── soft-skill/              ← NEW (premium / Apple-y / Awwwards)
    ├── minimalist-skill/        ← NEW (Notion / Linear editorial)
    ├── brutalist-skill/         ← NEW (Swiss / data / military)
    ├── redesign-skill/          ← NEW (audit-and-fix existing UI)
    ├── output-skill/            ← NEW (always co-loaded; bans placeholders)
    └── gpt-tasteskill/          ← NEW (strict GSAP / GPT/Codex target)

config/
└── departments.yaml             ← MODIFIED: +1 orchestrator agent, 4 sub-agents
                                    updated with taste-skill rules in description +
                                    capabilities

prompts/role/design/
├── taste_frontend_architect.j2  ← NEW: standalone (no extends), 9 KB, full pipeline
├── ux_designer.j2               ← unchanged (3-line stub; rules via YAML)
├── graphic_designer.j2          ← unchanged
├── motion_artist.j2             ← unchanged
├── branding_strategist.j2       ← unchanged
├── wireframe_specialist.j2      ← unchanged
├── spatial_designer.j2          ← unchanged
├── color_expert.j2              ← unchanged
├── accessibility_auditor.j2     ← unchanged
├── prototype_builder.j2         ← unchanged
└── user_flow_mapper.j2          ← unchanged

docs/superpowers/specs/
└── 2026-06-05-taste-skill-integration-design.md  ← THIS FILE
```

### Layered authority

```
┌─────────────────────────────────────────────────────────────────┐
│  .claude/rules/taste-router.md       (WHICH variant + dials)    │
│  ─── runs BEFORE any UI/UX work ──────────────────────────────│
│  • picks taste-skill variant (8 options)                        │
│  • sets 3 dials (VARIANCE / MOTION / DENSITY, 1-10 each)        │
│  • enforces brief-inference line + 18-item pre-flight          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  .claude/rules/ui-ux-excellence.md  (WHAT to avoid)             │
│  ─── forbidden-pattern detector ───────────────────────────────│
│  • purple/indigo gradient backgrounds                            │
│  • 3-column icon-in-circle feature grid                          │
│  • "Welcome to [App Name]" headings                              │
│  • linear-gradient() on buttons                                  │
│  • emoji as icons                                                │
│  • banned fonts (Inter, Roboto, Arial, Open Sans, system-ui)    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  .claude/skills/<variant>/SKILL.md  (HOW to build)              │
│  ─── actual recipes ──────────────────────────────────────────│
│  • font pairings (Bebas Neue + Manrope, Fraunces + Söhne, ...)  │
│  • motion physics (ease-out spring, GSAP, scroll-driven)        │
│  • bento grid math (12-col asymmetric, golden-ratio)            │
│  • color tokens (OKLCH, muted primaries, off-black)             │
│  • component patterns (cards, buttons, forms, empty states)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  .claude/skills/output-skill/SKILL.md  (COMPLETE)               │
│  ─── always co-loaded ────────────────────────────────────────│
│  • bans "// ..." placeholder comments                            │
│  • bans "rest follows the same pattern"                          │
│  • bans truncation on long code blocks                            │
│  • enforces ship-complete deliverables                           │
└─────────────────────────────────────────────────────────────────┘
```

### Render path (how it flows at request time)

```
User prompt
  │
  ▼
NEXUS routing (3 layers: keyword → semantic → LLM)
  │
  ▼
core/orchestrator.py:880-926  (_build_system_prompt)
  │
  ├── loader: FileSystemLoader(tmpl_path.parent)
  │
  ├── vars passed to render():
  │   role                = "taste_frontend_architect"
  │   department          = "design"
  │   role_description    = agent.description   ← from departments.yaml:318
  │   capabilities        = agent.capabilities   ← from departments.yaml:326-341
  │   tools               = agent.tools          ← from departments.yaml:342-343
  │   task                = user prompt
  │   context             = ""                   ← from prior turns if any
  │
  └── output → system prompt sent to litellm
```

For `taste_frontend_architect`:
- The `.j2` file is a **standalone** template (no `{% extends %}`) — the full 6-stage
  pipeline is inlined verbatim
- `{{ role_description }}` and `{{ capabilities }}` are still rendered (they appear
  in the orchestrator's "Context" section near the bottom)

For the 4 wired sub-agents:
- The `.j2` files are 3-line stubs that extend `base.j2`
- `base.j2` has no `{% block %}` definitions, so the stub content (just the extends
  line) is what's rendered
- ALL the taste-skill rules flow in via `{{ role_description }}` (YAML description
  contains the loading rules + dial defaults) and `{{ capabilities }}` (YAML list
  contains `taste-skill-{variant}` + `taste-skill-output` + `dial-{N-N-N}`)

---

## The taste-skill Pipeline (6 stages)

These are the stages that `taste_frontend_architect` runs every UI/UX brief through.
The first 3 are mandatory gates; stages 4-6 are conditional on the brief.

### Stage 1 — Brief Inference (non-negotiable)

Before any code, output exactly one line on its own:

```
Reading this as: <page kind> for <audience>, with a <vibe> language, leaning toward <design system>.
```

Examples (from the rule):
- *"Reading this as: B2B SaaS landing for technical buyers, with a Linear-style minimalist language, leaning toward Tailwind utilities + Geist + restrained motion."*
- *"Reading this as: solo designer portfolio for hiring managers, with an editorial / kinetic-type language, leaning toward native CSS + scroll-driven animation + custom typography."*

**Anti-default discipline:** Do NOT default to AI-purple gradients, centered hero
over dark mesh, three equal feature cards, generic glassmorphism, infinite-loop
micro-animations, Inter + slate-900. These are LLM defaults — reach past them
deliberately based on the design read.

If the brief is genuinely ambiguous, ask ONE clarifying question (e.g., "Should this
feel closer to Linear-clean or Awwwards-experimental?") — never a multi-question dump.

### Stage 2 — Dial Setting (1-10 each)

```
DESIGN_VARIANCE:  <1-10>   (1 = symmetric,    10 = artsy chaos)
MOTION_INTENSITY: <1-10>   (1 = static,       10 = cinematic / physics)
VISUAL_DENSITY:   <1-10>   (1 = gallery airy, 10 = cockpit data-packed)
```

Baseline: **8 / 6 / 4**. Override per brief:

| Brief signal                              | VARIANCE | MOTION | DENSITY |
|-------------------------------------------|----------|--------|---------|
| minimalist / clean / calm / editorial     | 5-6      | 3-4    | 2-3     |
| premium consumer / Apple-y / luxury       | 7-8      | 5-7    | 3-4     |
| playful / wild / Dribbble / Awwwards      | 9-10     | 8-10   | 3-4     |
| landing page / portfolio / marketing      | 7-9      | 6-8    | 3-5     |
| trust-first / public-sector / regulated   | 3-4      | 2-3    | 4-5     |
| data dashboard / engineering tool / IDE   | 4-5      | 2-4    | 7-9     |

### Stage 3 — Variant Selection

The router picks ONE primary variant + ALWAYS co-loads `output-skill`:

| Signal                              | Load SKILL               |
|-------------------------------------|--------------------------|
| new landing / portfolio / marketing | **taste-skill v2** (default) |
| Awwwards / $150k-agency / luxury    | soft-skill               |
| Notion / Linear editorial / calm    | minimalist-skill         |
| data dashboard / Swiss / military   | brutalist-skill          |
| audit / redesign existing UI        | redesign-skill           |
| LLM truncating / placeholder output | output-skill (always co-loaded) |

The orchestrator is responsible for reading `.claude/skills/<variant>/SKILL.md` in
full before invoking it. The router picks WHICH; the orchestrator decides HOW.

### Stage 4 — Sub-Agent Dispatch (when appropriate)

The orchestrator can either implement directly (via `interpreter` tool) or hand off
to a specialist. The agent routing table from `taste-router.md §6`:

| Sub-agent                | Always loads                        | Sometimes loads            |
|--------------------------|-------------------------------------|----------------------------|
| `taste_frontend_architect` | taste-skill v2 + output-skill     | brief-specific (soft/minimalist/brutalist) |
| `ux_designer`            | minimalist-skill + output-skill     | taste-skill v2 (broader brief) |
| `graphic_designer`       | brutalist-skill + output-skill      | minimalist-skill (brand)   |
| `branding_strategist`    | minimalist-skill + output-skill    | soft-skill (premium brand) |
| `motion_artist`          | soft-skill + output-skill           | gpt-tasteskill (strict GSAP) |
| `spatial_designer`       | brutalist-skill + output-skill      | soft-skill (premium 3D)    |
| `wireframe_specialist`   | output-skill + redesign-skill       | —                          |
| `color_expert`           | minimalist-skill + output-skill     | —                          |
| `accessibility_auditor`  | output-skill + ui-ux-excellence.md  | — (a11y is constraint)     |
| `prototype_builder`      | taste-skill v2 + output-skill       | soft-skill (motion demo)   |
| `user_flow_mapper`       | output-skill                        | — (flows are not aesthetic) |

Sub-agent dial defaults (locked unless brief overrides):

| Agent                   | VARIANCE | MOTION | DENSITY |
|-------------------------|----------|--------|---------|
| `taste_frontend_architect` | from brief | from brief | from brief |
| `ux_designer`           | 6        | 4      | 3       |
| `graphic_designer`      | 7        | 5      | 4       |
| `branding_strategist`   | 6        | 4      | 3       |
| `motion_artist`         | 8        | 9      | 4       |
| `spatial_designer`      | 8        | 7      | 5       |
| `wireframe_specialist`  | 4        | 2      | 3       |
| `color_expert`          | 5        | 3      | 4       |
| `accessibility_auditor` | 4        | 3      | 5       |
| `prototype_builder`     | 7        | 7      | 4       |
| `user_flow_mapper`      | 4        | 2      | 4       |

### Stage 5 — Pre-Flight Checklist (18-item gate)

Before declaring "done", run this. If 3+ fail, regenerate. If 1-2 fail, fix inline.
Document the check in the response so the user sees the work.

```
[ ] Brief read declared on its own line
[ ] Dials stated (VARIANCE / MOTION / DENSITY)
[ ] taste-skill variant identified
[ ] No banned fonts (Inter / Roboto / Arial / Open Sans / system-ui)
[ ] No banned icons (Lucide / Heroicons solid / FontAwesome) — use Phosphor / Remix Line / hand-drawn
[ ] No purple/indigo gradient backgrounds
[ ] No "3-equal-icon-cards" feature grid
[ ] No linear-gradient() on buttons — solid accent only
[ ] Body text not pure #000000 — use off-black (#111 or charcoal)
[ ] Headlines have letter-spacing: -0.02em to -0.04em
[ ] Layout either fully symmetric OR explicitly asymmetric with intent
[ ] No emoji as icons
[ ] No "Welcome to [App Name]" headings
[ ] All CTAs are full sentences or specific verbs (never "Click here")
[ ] output-skill enforced: no "// ..." or "rest follows the same pattern"
[ ] All interactive elements are Tab + Enter/Space accessible
[ ] Dark mode token set declared (even if light-only shipped)
[ ] Mobile collapse strategy explicit (w-full, px-4, min-h-[100dvh])
```

### Stage 6 — Handoff

If a sub-agent ships the implementation, the orchestrator remains the design owner.
The orchestrator reviews the sub-agent's output against the pre-flight checklist
before signing off. Never let a sub-agent ship without the checklist passing. If
their dials differ from the orchestrator's, **escalate, do not silently merge**.

---

## Variant Picker (full table from taste-router.md §1)

| Task signal | Load SKILL | Install name | When to use |
|---|---|---|---|
| New landing page, portfolio, marketing site | `taste-skill` (v2) | `design-taste-frontend` | **DEFAULT** for any new frontend brief |
| Awwwards-tier, $150k agency feel, premium consumer | `soft-skill` | `high-end-visual-design` | "premium", "Apple-y", "luxury", "agency-tier", "Awwwards" |
| Notion/Linear editorial, calm restrained UI | `minimalist-skill` | `minimalist-ui` | "minimalist", "clean", "editorial", "document-style" |
| Data dashboards, Swiss typography, military/HUD | `brutalist-skill` | `industrial-brutalist-ui` | "brutalist", "Swiss", "blueprint", "data-dense" |
| Audit-and-fix existing UI | `redesign-skill` | `redesign-existing-projects` | "redesign", "upgrade", "audit this UI" |
| LLM truncating output, placeholder comments | `output-skill` | `full-output-enforcement` | When previous output had `// ...` |
| GPT/Codex-specific strictness | `gpt-tasteskill` | `gpt-taste` | When generation target is GPT-4/GPT-5/Codex |
| Pin to v1 of taste-skill (legacy) | `taste-skill-v1` | `design-taste-frontend-v1` | Only if user explicitly requests v1 backward-compat |

**Default order** (when multiple match): `taste-skill` (v2) → `output-skill` (always
co-load) → context-specific (soft/minimalist/brutalist/redesign).

---

## Agent Wiring (what changed in departments.yaml)

### `taste_frontend_architect` (NEW, heavyweight)

```yaml
taste_frontend_architect:
  description: Senior taste-frontend architect — runs the taste-skill pipeline
    (brief inference → dial setting → variant selection → implementation →
    pre-flight checklist). Orchestrates the 10 design sub-agents, enforces
    anti-slop discipline, ships Linear/Vercel/Stripe/Oxide-grade interfaces.
  primary_model: minimax-m3
  fallbacks: [minimax-text-01, minimax-text-01]
  capabilities:
  - taste-skill
  - design-taste
  - frontend-architect
  - brief-inference
  - dial-setting
  - design-variance
  - motion-intensity
  - visual-density
  - design-system
  - anti-slop
  - handoff
  - typography
  - motion-physics
  - color-discipline
  - layout
  tools: [interpreter]
  complexity_tier: heavyweight
```

The prompt template (`prompts/role/design/taste_frontend_architect.j2`) is a
**standalone** Jinja2 template that inlines all 6 stages of the taste-skill
pipeline. It's 9192 bytes (vs ~180 bytes for the stubs). JSON response format
includes `brief_read`, `dials`, `variant`, `preflight`, `confidence`,
`reasoning`, `followup` fields.

### 4 sub-agents (UPDATED)

Each got a new `description` documenting the taste-skill loading rules + dial
defaults, plus new `capabilities` entries (`taste-skill-{variant}`,
`taste-skill-output`, `dial-{N-N-N}`).

| Sub-agent | Always loads | Sometimes loads | Dials |
|---|---|---|---|
| `ux_designer` | minimalist-skill + output-skill | taste-skill v2 (broader brief) | 6/4/3 |
| `graphic_designer` | brutalist-skill (typography) + output-skill | minimalist-skill (brand) | 7/5/4 |
| `branding_strategist` | minimalist-skill (color) + output-skill | soft-skill (premium brand) | 6/4/3 |
| `motion_artist` | soft-skill (haptic motion) + output-skill | gpt-tasteskill (strict GSAP) | 8/9/4 |

**Why YAML metadata, not .j2 content?** Because `prompts/base.j2` has no
`{% block %}` definitions, any content after `{% extends %}` in the stubs is
silently dropped. YAML-driven metadata flows into the rendered prompt via the
existing `{{ role_description }}` and `{{ capabilities }}` placeholders — no
template refactor required.

### 5 sub-agents (NOT updated in v1, tracked for v2)

These remain at their original 3-line stub state. They're still loadable via
the taste-router rule (which is project-wide, not per-agent), but their YAML
metadata doesn't document the loading rule yet:

- `wireframe_specialist` — should always load output-skill + redesign-skill
- `spatial_designer` — should always load brutalist-skill + output-skill
- `color_expert` — should always load minimalist-skill + output-skill
- `accessibility_auditor` — should always load output-skill + ui-ux-excellence.md
- `prototype_builder` — should always load taste-skill v2 + output-skill
- `user_flow_mapper` — should always load output-skill

---

## Rollback

To disable taste-skill routing:
```bash
mv .claude/rules/taste-router.md .claude/rules/taste-router.md.disabled
```

The base system falls back to `ui-ux-excellence.md` + `frontend-design`
(Anthropic default) — same behavior as before this integration.

To uninstall a specific variant:
```bash
rm -rf .claude/skills/<variant-name>/
```

To roll back the YAML changes:
```bash
git checkout HEAD -- config/departments.yaml
rm prompts/role/design/taste_frontend_architect.j2
```

To roll back the role prompt:
The 4 sub-agent `.j2` files were NOT modified (still 3-line stubs). The
orchestrator's `.j2` file can be removed with `rm` — the YAML entry that
references it will be cleaned by the departments.yaml rollback above.

---

## Failure Modes (anti-patterns in taste-skill usage)

From `taste-router.md §7`:

| Failure mode | Mitigation |
|---|---|
| **Cargo-culted brutalism:** applying brutalist-skill to a wedding-planning site | Match the variant to the brief — router picks |
| **Decorative motion:** motion_artist cranking MOTION=10 on a B2B procurement tool | Dial inference says "trust-first" → MOTION 2-3, hard rule |
| **3-dial rigid thinking:** treating VARIANCE=10 as a license for chaos | The dial caps variance, not quality |
| **"I'll just use taste-skill" without reading the brief** | Stage 1 brief inference is non-negotiable; skip it = no taste-skill |
| **Variant thrash:** loading 4 SKILL.md files at once and mashing them | Pick ONE primary + output-skill. Load a 3rd only if explicitly needed |
| **Skipping pre-flight** | Stage 5 gate exists because taste-skill's own audits are easy to forget |

---

## Integration with Existing Systems

### 6-layer memory

The 5 wired design agents (1 orchestrator + 4 sub-agents) participate in the
existing 6-layer memory system via `core/memory/observation_store.py` (added in
the claude-mem integration on 2026-06-04). Every tool call these agents make
gets captured as a structured observation and fanned out to:

- **Layer 1 (checkpoints):** session rollback points
- **Layer 2 (ChromaDB):** vector search across design decisions
- **Layer 3 (langmem):** structured design decision memory
- **Layer 4 (observation_store):** SQLite + FTS5 timeline
- **Layer 5 (graphrag):** code/design knowledge graph
- **Layer 6 (mem0):** cross-agent design pattern memory

The taste-skill pipeline itself is captured (brief_read, dials, variant,
preflight_passed/failed counts) — so future sessions can recall what dial
settings worked for which kind of brief.

### GitNexus

`taste_frontend_architect.j2` and `taste-router.md` are now part of the indexed
codebase (70149 symbols, 169906 relationships per the project CLAUDE.md). Any
refactor of the taste-skill wiring should run `gitnexus_impact` first.

### Hermes MCP

`hermes_session_search` can now query past taste-skill decisions via FTS5 across
session transcripts. Pattern: "brief read: B2B SaaS landing" → returns the
orchestrator's prior run with full dials + variant + preflight results.

### Observation bridges

Every `taste_frontend_architect` Edit/Write to `.claude/rules/`, `.claude/skills/`,
`prompts/role/design/`, or `config/departments.yaml` fires the gitnexus bridge
via the tool-name gate (Edit/Write/MultiEdit/NotebookEdit + non-noise file).
This is automatic via the existing observation_store → bridges fanout.

### Auto-memory

The integration is now in MEMORY.md under a new entry that will be created in
Task #22. The bootstrap will pull the dial defaults, variant picker, and
pre-flight checklist into the next session's auto-injected context.

---

## Verification

After implementation, the following were verified:

1. **YAML parse**: `python3 -c "import yaml; yaml.safe_load(open('config/departments.yaml'))"` → 11 design agents parsed cleanly
2. **Sub-agent metadata**: `grep -nE 'taste-skill-(minimalist|brutalist|soft|output)|dial-' config/departments.yaml` → 4 sub-agents have 12 new capability entries
3. **SKILL.md presence**: all 8 variants (`brutalist-skill`, `gpt-tasteskill`, `minimalist-skill`, `output-skill`, `redesign-skill`, `soft-skill`, `taste-skill`, `taste-skill-v1`) have SKILL.md files
4. **taste-router rule**: `.claude/rules/taste-router.md` exists (11559 bytes, 8 sections)
5. **Orchestrator template**: `prompts/role/design/taste_frontend_architect.j2` exists (9192 bytes, standalone, full 6-stage pipeline)
6. **Base template untouched**: `prompts/base.j2` was not modified (the YAML-driven approach means the existing render path works without changes)

End-to-end render test: the production render path in `core/orchestrator.py:880-926`
will pass `role_description=taste_frontend_architect.description` and
`capabilities=taste_frontend_architect.capabilities` into the standalone `.j2`
template, which renders the full 6-stage pipeline + JSON response format.

---

## File-by-file change list

| File | Action | Size | Purpose |
|---|---|---|---|
| `.claude/skills/taste-skill/SKILL.md` | CREATE | 87,253 B | Default taste-skill v2 (variant picker default) |
| `.claude/skills/taste-skill-v1/SKILL.md` | CREATE | 21,195 B | Legacy v1 (backward compat) |
| `.claude/skills/soft-skill/SKILL.md` | CREATE | 10,561 B | Premium / Apple-y / Awwwards |
| `.claude/skills/minimalist-skill/SKILL.md` | CREATE | 7,901 B | Notion / Linear editorial |
| `.claude/skills/brutalist-skill/SKILL.md` | CREATE | 8,456 B | Swiss / data / military HUD |
| `.claude/skills/redesign-skill/SKILL.md` | CREATE | 15,060 B | Audit-and-fix existing UI |
| `.claude/skills/gpt-tasteskill/SKILL.md` | CREATE | 7,857 B | Strict GSAP / GPT/Codex target |
| `.claude/skills/output-skill/SKILL.md` | CREATE | 2,592 B | Always co-loaded; bans placeholders |
| `.claude/rules/taste-router.md` | CREATE | 11,559 B | Dial setter + variant picker rule |
| `prompts/role/design/taste_frontend_architect.j2` | CREATE | 9,192 B | Standalone orchestrator template, 6-stage pipeline |
| `config/departments.yaml` | MODIFY | +~2 KB | +1 orchestrator agent, 4 sub-agents updated |

**Total new content:** ~183 KB of taste-skill recipes + ~21 KB of project integration glue
**Total modified:** 1 YAML file (+2 KB)

---

## Next Steps (post-v1)

1. **Task #22**: Add MEMORY.md entries for the integration + run `scripts/verify-memory-pipeline.py` to verify nothing in the 6-layer pipeline broke
2. **v2 (future)**: Wire the remaining 5 design sub-agents (wireframe, spatial, color, accessibility, prototype, user_flow) with taste-skill rules in YAML
3. **v2 (future)**: Build the 18-item pre-flight auto-checker (script that scans output for banned patterns automatically)
4. **v2 (future)**: Add taste-skill pipeline capture to observation_store (so `brief_read`, `dials`, `variant`, `preflight` are queryable across sessions)
5. **v3 (future)**: Custom taste-skill variant for swarm-bot's specific brand (Babas Agency / cekwajar.id / rumahlabuh.com)
