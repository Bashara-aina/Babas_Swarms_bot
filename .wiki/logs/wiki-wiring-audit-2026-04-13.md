---
title: Wiki Wiring Audit 2026 04 13
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Files Analyzed: 1073 (excluding quarantine)'
wikilinks: []
confidence: medium
source: research
---
## Wiki Wiring Audit Report
Date: 2026-04-13
Status: COMPLETE
Files Analyzed: 1073 (excluding quarantine)
Broken Wikilinks Found: 119

---

## Issue Summary

| Category | Count | Fix Approach |
|----------|-------|--------------|
| Missing concept files (links to non-existent) | 16 | Create stub files or fix link paths |
| Wrong path links (`wiki/` prefix) | 10 | Remove `wiki/` prefix |
| Template placeholders | 14 | Remove or replace |
| Directory-style links (`/`) | 7 | Remove trailing slash |
| Core code path references | 12 | Convert to code paths or remove |
| Legitimate entity/concept links needing prefix | 15 | Add `./` or path prefix |
| YAML frontmatter issue | 1 | Fix malformed YAML |
| Stub/test links | 12 | Remove |
| Other | 32 | Case-by-case |

---

## Issues by Category

### Category 1: Missing Concept Files
Files that should exist in `./concepts/` but are also linked without path:
- `bayesian-blending` → exists at `./concepts/bayesian-blending.md` — fix links to use path
- `bpjs-reference` → exists at `./concepts/bpjs-reference.md` — fix links
- `intent-router` → does NOT exist, should be `intent-routing`
- `context-window-budget` → exists at `./concepts/context-window-budget.md` — fix links
- `freemium-gate` → exists at `./concepts/freemium-gate.md` — fix links
- `karpathy-kb-pattern` → exists at `./concepts/karpathy-kb-pattern.md` — fix links
- `labor-law-indonesia` → exists at `./concepts/labor-law-indonesia.md` — fix links
- `litellm` → exists at `./entities/litellm.md` — fix links to use path
- `llm-cost-routing` → exists at `./concepts/llm-cost-routing.md` — fix links
- `market-data-indonesia` → exists at `./concepts/market-data-indonesia.md` — fix links
- `multi-agent-orchestration` → exists at `./concepts/multi-agent-orchestration.md` — fix links
- `reasoning-loop` → exists at `./concepts/reasoning-loop.md` — fix links
- `self-improvement-loop` → exists at `./concepts/self-improvement-loop.md` — fix links
- `skill-registry` → exists at `./concepts/skill-registry.md` — fix links
- `tax-indonesia` → exists at `./concepts/tax-indonesia.md` — fix links
- `vector-search` → exists at `./concepts/vector-search.md` — fix links

### Category 2: Wrong Path Links (wiki/ prefix)
- `wiki/INDEX` → `INDEX`
- `wiki/SCHEMA.md` → `SCHEMA.md`
- `wiki/conversations.md` → `conversations` (if exists)
- `wiki/conversations/support.md` → `conversations/support` (if exists)
- `wiki/legion/conversation_processing.md` → `legion/conversation_processing` (if exists)
- `wiki/legion/faq.md` → `legion/faq` (if exists)
- `wiki/legion/interactions.md` → `legion/interactions` (if exists)
- `wiki/mental_health.md` → `mental_health` (if exists)
- `wiki/research/_template` → `research/_template`
- `.wiki/decisions/ADR-001-opencode-integration.md` → `decisions/ADR-001-opencode-integration`

### Category 3: Template Placeholders (remove or replace)
Found in test fixtures and skill templates:
- `Architecture Review`, `Book Notes - Thinking in Systems`, `Concept Name`, `Concept1`
- `Entity Name`, `Entity1`, `Entity2`, `Journal 2026-04-09`, `Personal Growth`
- `Project Alpha`, `Security Audit`, `Short Notes`, `Source - Article Title`, `Team Meetings`

### Category 4: Directory-style Links (trailing /)
- `agents/`, `architecture/`, `decisions/`, `issues/`, `logs/`, `prompts/`, `research/`

### Category 5: Core/Code Path References
These reference code modules, not wiki pages:
- `core/daily_harvester/harvest-pipeline`, `core/daily_harvester/scorer`, `core/intent-classifier`
- `core/intent_router`, `core/memory/memory_manager`, `core/nexus_orchestrator`
- `core/soul_engine`, `core/task_orchestrator`, `handlers/harvest-review`
- `legion/harvester/harvest-log`, `data/beliefs.json`

### Category 6: Legitimate Links Needing Path Prefix
Entity/concept links without path prefix:
- `opencode`, `cursor`, `supabase`, `dify`, `chromadb`, `gpt-researcher`
- `openrouter`, `minimax-m2-7`, `midtrans`

### Category 7: YAML Frontmatter Issue
- `logs/planner-2026-04-13-hallucination-fix-contracts-batch1.md` — malformed backtick in YAML

---

## Recommendations

1. **Batch fix path prefix issues** — Most broken links are valid wiki pages with wrong path format
2. **Create stub files for referenced but missing content** — Some links reference content that should exist
3. **Remove template placeholders from test fixtures** — These are test data, not real links
4. **Fix YAML frontmatter** — One file has malformed frontmatter preventing parsing
5. **Convert code path references** — These should be code-style paths or external URLs, not wikilinks

---

*Report generated: 2026-04-13*