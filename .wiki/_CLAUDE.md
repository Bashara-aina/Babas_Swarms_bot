# Claude Operating Manual — Bashara's Vault

> Read this file before doing anything in this vault.
> This is the single source of truth for how Claude operates here.

---

## Section 0 — AI-First Vault Rule (read first, applies to every note)

This vault is designed for **future-Claude** to read and reason over, not for human review. The owner rarely reads notes directly — they call Claude to retrieve, synthesize, and connect dots across years of accumulated knowledge.

**Every note Claude writes to this vault must follow these rules:**

1. **Self-contained context** — Each note must explain itself. Future-Claude may pull this single note via search with no surrounding context. Don't rely on backlinks alone for meaning.
2. **"For future Claude" preamble** — Every note begins with a 2-3 sentence summary in plain English so Claude can decide relevance in 10 seconds before parsing the structured data.
3. **Rich, consistent frontmatter** — Filterable metadata (`type`, `date`, `topic`, `tags`, `related-people`, `related-projects`, `sources`, `confidence`). Different note types may have different schemas, but every note has machine-readable frontmatter.
4. **Recency markers per claim** — When stating external facts, attach the date: "Mem0 raised $24M (as of 2026-04)" so future-Claude knows what to verify before trusting.
5. **Sources preserved verbatim** — Every external claim has its source URL inline so it can be re-verified or refreshed.
6. **Cross-links are mandatory** — Every person, project, idea, decision, or concept referenced uses `[[wikilinks]]` so the graph is traversable.
7. **Confidence levels** — Where applicable, mark claims as `stated | high | medium | speculation` so future-Claude knows what to trust vs verify.

This rule applies to all `/obsidian-*` and `/research*` commands, all scheduled agents, and any direct vault writes.

---

## Vault Identity

- **Owner:** Bashara (newadmin)
- **Primary purpose:** Swarm-bot Operations — AI agent orchestration system development, configuration, and knowledge base
- **Last updated:** 2026-05-08

---

## Folder Map

| Folder | Purpose |
|---|---|
| `Daily/` | One note per day. Named `YYYY-MM-DD.md` |
| `Projects/` | Active and archived projects (swarm-bot, cekwajar, rumahlabuh, etc.) |
| `People/` | One note per person (collaborators, agents, team members) |
| `Ideas/` | Brainstorms, RFCs, and early-stage proposals |
| `Boards/` | Kanban boards for project tracking |
| `Dev Logs/` | Technical work logs — dated, project-tagged |
| `Work/` | Active task notes and work-in-progress |
| `Archive/` | Archived notes (prefix: `_archived_`) |
| `knowledge/` | Reference material and permanent notes |
| `reference/` | External references, guides, documentation |
| `brain/` | Neural patterns, memory architecture docs |
| `legion/` | Legion agent system documentation |

---

## Key Files

- **Dashboard:** `[[Home]]` — main navigation
- **Agent Registry:** [agents/agent-registry](agents/agent-registry.md) or `core/agent_registry.py`
- **Memory Architecture:** `[[memory-architecture]]`
- **Intent Routing:** `[[intent-routing-map]]`
- **Projects Index:** [projects/](projects/) folder

---

## Active Context

**Current top priority:** Integrate obsidian-second-brain framework into OpenCode session workflow
**Current project:** swarm-bot — 76+ agent Telegram bot orchestration system
**Key system components:** core/agent_registry.py, handlers/, tools/, config/models.yaml

---

## Auto-Save Rules

Claude should auto-save the following **without asking**:
- Decisions made in conversation → relevant project note + daily note
- New people mentioned → People/ (create stub if needed)
- Tasks assigned or committed to → kanban board + Tasks/ note
- Dev work done → Dev Logs/ + project note + daily note
- Agent configuration changes → relevant config file + daily note
- Mention/recognition from colleagues → Mentions Log + person's note + daily note
- Completed tasks → move on kanban to ✅ Done

Claude should **ask before saving**:
- Anything touching Finances/ or personal financial data
- Anything that involves deleting or archiving an existing note
- Production configuration changes without user confirmation

---

## Naming Conventions

- Daily notes: `YYYY-MM-DD.md`
- Dev logs: `YYYY-MM-DD — Description.md`
- Projects: Descriptive title (e.g. `swarm-bot-agent-registry.md`)
- People: Full name (e.g. `Bashara.md`)
- Archive prefix: `_archived_`

---

## Frontmatter Requirements

Every note must have at minimum:
```yaml
---
date: YYYY-MM-DD
tags:
  - [note-type]
---
```

Note types: `daily` | `project` | `task` | `person` | `devlog` | `idea` | `decision` | `agent` | `config`

---

## Propagation Rules

| Event | Also update |
|---|---|
| New project | Board (Backlog) + today's daily note |
| Task done | Board (Done, strikethrough) + project note + daily note |
| Dev session | Dev Logs/ + project note (Recent Activity) + daily note |
| Person interaction | Daily note + their People/ note |
| Decision made | Project note (Key Decisions) + daily note |
| Agent config change | Dev Logs/ + relevant config file + daily note |

---

## Projects Currently Active

- [swarm-bot](projects/legion-bot.md) — 76+ agent Telegram bot orchestration system
- [cekwajar](projects/cekwajar-id.md) — Indonesian employment/job seeker assistance project
- [rumahlabuh](projects/rumahlabuh-com.md) — Boarding house/rental management project

---

## Do Not Touch

- `Templates/` — Never modify templates during normal vault operations
- `config/` — Core configuration files without backup
- Production credentials and API keys in any file

---

*This file was generated by the obsidian-second-brain skill.*
*Regenerate with: "Claude, update my _CLAUDE.md"*
