## Plan: Wiki Wiring Audit — Fix Broken Links and References
Date: 2026-04-13
Type: REFACTOR (wiki wiring fix)
Context gathered:
- 2156 total .md files in .wiki
- 1073 non-quarantine .md files
- 119 broken wikilinks found (excluding research paper refs and quarantine)
- 749 potentially orphaned files

## Issues Catalog

### Category 1: Missing Concept Files (should exist in ./concepts/)
These files are referenced but don't exist:
- `bayesian-blending` (linked from concepts/llm-cost-routing.md)
- `bpjs-reference` (linked from architecture/cekwajar-verdict-engine.md)
- `intent-router` (no such file — should be `intent-routing`)
- `context-window-budget` (linked from concepts/llm-cost-routing.md)
- `freemium-gate` (linked from architecture/cekwajar-verdict-engine.md)
- `karpathy-kb-pattern` (linked from SCHEMA.md, people/andrej-karpathy.md)
- `labor-law-indonesia` (linked from concepts/tax-indonesia.md)
- `litellm` (linked from SCHEMA.md)
- `llm-cost-routing` (linked from people/andrej-karpathy.md)
- `market-data-indonesia` (linked from architecture/cekwajar-data-sources.md)
- `multi-agent-orchestration` (linked from architecture/orchestrator-comparison.md)
- `reasoning-loop` (linked from architecture/legion-daily-harvester.md)
- `self-improvement-loop` (linked from people/andrej-karpathy.md)
- `skill-registry` (linked from architecture/skill-execution-flow.md)
- `tax-indonesia` (linked from architecture/cekwajar-verdict-engine.md)
- `vector-search` (linked from people/andrej-karpathy.md)

### Category 2: Wrong Path Links (wiki/ prefix)
These links have `wiki/` or `.wiki/` prefix that should be removed:
- `wiki/INDEX` → should be `INDEX`
- `wiki/SCHEMA.md` → should be `SCHEMA.md`
- `wiki/conversations.md` → should be `conversations` (if exists)
- `wiki/conversations/support.md` → should be `conversations/support`
- `wiki/legion/conversation_processing.md` → should be `legion/conversation_processing`
- `wiki/legion/faq.md` → should be `legion/faq`
- `wiki/legion/interactions.md` → should be `legion/interactions`
- `wiki/mental_health.md` → should be `mental_health`
- `wiki/research/_template` → should be `research/_template`
- `.wiki/decisions/ADR-001-opencode-integration.md` → should be `decisions/ADR-001-opencode-integration`

### Category 3: Template Placeholders (should be removed or replaced)
- `Architecture Review` — template placeholder
- `Book Notes - Thinking in Systems` — template placeholder
- `Concept Name` — template placeholder
- `Concept1` — template placeholder
- `Entity Name` — template placeholder
- `Entity1` — template placeholder
- `Entity2` — template placeholder
- `Journal 2026-04-09` — template placeholder
- `Personal Growth` — template placeholder
- `Project Alpha` — template placeholder
- `Security Audit` — template placeholder
- `Short Notes` — template placeholder
- `Source - Article Title` — template placeholder
- `Team Meetings` — template placeholder

### Category 4: Directory-style Links (links ending with /)
- `agents/` → should be `agents` or removed
- `architecture/` → should be `architecture` or removed
- `decisions/` → should be `decisions` or removed
- `issues/` → should be `issues` or removed
- `logs/` → should be `logs` or removed
- `prompts/` → should be `prompts` or removed
- `research/` → should be `research` or removed

### Category 5: Legitimate Links That Need Root Path Fixes
Some links work if prefixed with `./` but wikilinks may not resolve without it:
- `opencode` (should be `./entities/opencode`)
- `cursor` (should be `./entities/cursor`)
- `supabase` (should be `./entities/supabase`)
- `dify` (should be `./entities/dify`)
- `chromadb` (should be `./entities/chromadb`)
- `gpt-researcher` (should be `./entities/gpt-researcher`)
- `openrouter` (should be `./entities/openrouter`)
- `minimax-m2-7` (should be `./entities/minimax-m2-7`)

### Category 6: YAML Frontmatter Issue
- `logs/planner-2026-04-13-hallucination-fix-contracts-batch1.md` has malformed YAML (backtick in field)

### Category 7: Other Broken Links
- `...` (ellipsis link) — should be removed
- `054b-cutmix-2020` — research paper link not resolved
- `2025-11-17 - Matryoshka embeddings` — not a wiki link
- `<source note title>` — template placeholder
- `Bashara-aina` — appears to be a person/alias reference, needs verification
- `link`, `link1`, `link2`, `link3` — test/template links
- `related-page-1`, `related-page-2` — stub links
- `path.md` — stub link
- `slug` — template placeholder
- `source note` — template placeholder
- `task` — template placeholder
- `article-name` — template placeholder
- `decisions/popw-conference-strategy` — file doesn't exist (popw-conference not in decisions)
- `decisions/popw-pdd-pivot` — file doesn't exist
- `midtrans` — entity not in ./entities/ folder
- `core/daily_harvester/harvest-pipeline` — code path, not wiki path
- `core/daily_harvester/scorer` — code path, not wiki path
- `core/intent-classifier` — code path, not wiki path
- `core/intent_router` — code path, not wiki path
- `core/memory/memory_manager` — code path, not wiki path
- `core/nexus_orchestrator` — code path, not wiki path
- `core/soul_engine` — code path, not wiki path
- `core/task_orchestrator` — code path, not wiki path
- `handlers/harvest-review` — code path, not wiki path
- `legion/harvester/harvest-log` — code path, not wiki path
- `data/beliefs.json` — data file, not wiki
- `timelines/conversations_log` → should be `timelines/legion-version-history` or similar

## Risk Assessment
- Most issues are simple text replacements (wikilinks)
- Some may require creating stub files if the link target should exist but doesn't
- YAML frontmatter fix requires careful editing

## Approach
1. Batch 1: Fix wrong-path links (wiki/ prefix) — highest impact
2. Batch 2: Fix directory-style links and template placeholders — moderate impact
3. Batch 3: Fix broken references that need actual file creation (stub files) — lower priority
4. Batch 4: Fix YAML frontmatter issues