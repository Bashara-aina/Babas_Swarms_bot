# graphify
- **graphify** (`.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, invoke the Skill tool with `skill: "graphify"` before doing anything else.

# Design rules (load on demand only)
- UI/UX excellence + taste-router live in `.claude/reference/` (NOT auto-loaded — saves ~28 KB/session).
- When the user asks for a landing page, redesign, dashboard, or any visual/interaction work, Read both files first:
  - `.claude/reference/ui-ux-excellence.md` (forbidden patterns, component quality)
  - `.claude/reference/taste-router.md` (variant picker + 3-dial system)
- Do not auto-load them for non-UI work (Telegram bot logic, ML training, backend code, etc.).
