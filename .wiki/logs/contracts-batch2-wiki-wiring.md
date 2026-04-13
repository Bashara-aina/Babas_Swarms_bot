---
title: "Wiki Wiring Fix — Batch 2"
type: contract
status: active
tags: [wiring-fix, wiki]
created: 2026-04-13
summary: Fix broken concept/entity links by adding proper path prefix
---

## CONTRACT #4: Fix Concept Links Missing Path Prefix

WHAT:
  Fix 16 broken wikilinks to concept files by ensuring links use proper path prefix `./concepts/`

FILES:
  READ:
    - .wiki/concepts/llm-cost-routing.md
    - .wiki/architecture/cekwajar-verdict-engine.md
    - .wiki/people/andrej-karpathy.md
    - .wiki/concepts/tax-indonesia.md
    - .wiki/SCHEMA.md
    - .wiki/architecture/orchestrator-comparison.md
    - .wiki/architecture/legion-daily-harvester.md
    - .wiki/architecture/skill-execution-flow.md
  WRITE:
    - .wiki/concepts/llm-cost-routing.md
    - .wiki/architecture/cekwajar-verdict-engine.md
    - .wiki/people/andrej-karpathy.md
    - .wiki/concepts/tax-indonesia.md
    - .wiki/SCHEMA.md
    - .wiki/architecture/orchestrator-comparison.md
    - .wiki/architecture/legion-daily-harvester.md
    - .wiki/architecture/skill-execution-flow.md

DONE_WHEN:
  - `bayesian-blending` link in llm-cost-routing.md → `concepts/bayesian-blending`
  - `context-window-budget` link in llm-cost-routing.md → `concepts/context-window-budget`
  - `freemium-gate` links in cekwajar-verdict-engine.md → `concepts/freemium-gate`
  - `tax-indonesia` links in cekwajar-verdict-engine.md → `concepts/tax-indonesia`
  - `karpathy-kb-pattern` link in SCHEMA.md → `concepts/karpathy-kb-pattern`
  - `litellm` link in SCHEMA.md → `entities/litellm`
  - `supabase` link in SCHEMA.md → `entities/supabase`
  - `llm-cost-routing` links in andrej-karpathy.md → `concepts/llm-cost-routing`
  - `intent-routing` links in andrej-karpathy.md → `concepts/intent-routing`
  - `vector-search` link in andrej-karpathy.md → `concepts/vector-search`
  - `labor-law-indonesia` links in tax-indonesia.md → `concepts/labor-law-indonesia`
  - `market-data-indonesia` links in cekwajar-data-sources.md → `concepts/market-data-indonesia`
  - `multi-agent-orchestration` links in orchestrator-comparison.md → `concepts/multi-agent-orchestration`
  - `reasoning-loop` links in legion-daily-harvester.md → `concepts/reasoning-loop`
  - `skill-registry` links in skill-execution-flow.md → `concepts/skill-registry`
  - `self-improvement-loop` links in andrej-karpathy.md → `concepts/self-improvement-loop`

PROOF_FORMAT:
  Bash command: `python3 -c "
import re
files_to_check = [
    '.wiki/concepts/llm-cost-routing.md',
    '.wiki/architecture/cekwajar-verdict-engine.md',
    '.wiki/people/andrej-karpathy.md',
    '.wiki/concepts/tax-indonesia.md',
    '.wiki/SCHEMA.md',
]
broken = []
for f in files_to_check:
    try:
        content = open(f).read()
        # Check for bare concept names without path
        bare_names = ['bayesian-blending', 'context-window-budget', 'freemium-gate', 'tax-indonesia',
                      'karpathy-kb-pattern', 'litellm', 'supabase', 'llm-cost-routing', 
                      'intent-routing', 'vector-search', 'labor-law-indonesia', 'market-data-indonesia',
                      'multi-agent-orchestration', 'reasoning-loop', 'skill-registry', 'self-improvement-loop']
        for name in bare_names:
            # Match [[name]] not preceded by concepts/ or entities/
            pattern = rf'\[\[(?!concepts/|entities/){re.escape(name)}\]\]'
            if re.search(pattern, content):
                broken.append(f'{f}: {name}')
    except:
        pass
print('BROKEN' if broken else 'OK')
for b in broken:
    print(b)
"`

BLOCKER_IF:
  - Target file doesn't exist (concept entity not created yet)
  - Link is already correct

DEPENDS_ON: none

---

## CONTRACT #5: Fix Intent-Router Link (Non-existent File)

WHAT:
  Fix broken link `[[concepts/intent-router]]` — this file does not exist, should be `intent-routing`

FILES:
  READ:
    - .wiki/wisdom/domains/18-communication-writing.md
  WRITE:
    - .wiki/wisdom/domains/18-communication-writing.md

DONE_WHEN:
  - `[[concepts/intent-router]]` changed to `[[concepts/intent-routing]]`
  - File `concepts/intent-routing.md` exists (verified separately)

PROOF_FORMAT:
  Bash command: `grep -n "intent-router" .wiki/wisdom/domains/18-communication-writing.md`
  Expected output: no matches (link corrected)

BLOCKER_IF:
  - File doesn't exist

DEPENDS_ON: none

---

## CONTRACT #6: Fix Entity Links Missing Path Prefix

WHAT:
  Fix 9 broken wikilinks to entity files by ensuring links use proper path prefix `./entities/`

FILES:
  READ:
    - .wiki/architecture/memory-system-architecture.md
    - .wiki/concepts/memory-architecture.md
    - .wiki/entities/markitdown.md
    - .wiki/architecture/skill-execution-flow.md
    - .wiki/entities/litellm.md
    - .wiki/projects/legion-bot.md
    - .wiki/decisions/adr-2026-04-12-opencode-over-cursor-for-backend.md
  WRITE:
    - .wiki/architecture/memory-system-architecture.md
    - .wiki/concepts/memory-architecture.md
    - .wiki/entities/markitdown.md
    - .wiki/architecture/skill-execution-flow.md
    - .wiki/entities/litellm.md
    - .wiki/projects/legion-bot.md
    - .wiki/decisions/adr-2026-04-12-opencode-over-cursor-for-backend.md

DONE_WHEN:
  - `chromadb` bare link in memory-system-architecture.md → `entities/chromadb`
  - `chromadb` bare link in memory-architecture.md → `entities/chromadb`
  - `dify` bare link in markitdown.md → `entities/dify`
  - `gpt-researcher` bare link in skill-execution-flow.md → `entities/gpt-researcher`
  - `opencode` bare link in skill-execution-flow.md → `entities/opencode`
  - `openrouter` bare links in litellm.md → `entities/openrouter`
  - `cursor` bare links in adr-2026-04-12-opencode-over-cursor-for-backend.md → `entities/cursor`
  - `minimax-m2-7` bare link in projects/legion-bot.md → `entities/minimax-m2-7`

PROOF_FORMAT:
  Bash command: `python3 -c "
import re
files_to_check = [
    '.wiki/architecture/memory-system-architecture.md',
    '.wiki/concepts/memory-architecture.md',
    '.wiki/entities/markitdown.md',
    '.wiki/architecture/skill-execution-flow.md',
]
bare_entities = ['chromadb', 'dify', 'gpt-researcher', 'opencode', 'openrouter', 'cursor', 'minimax-m2-7']
broken = []
for f in files_to_check:
    try:
        content = open(f).read()
        for name in bare_entities:
            pattern = rf'\[\[(?!entities/){re.escape(name)}\]\]'
            if re.search(pattern, content):
                broken.append(f'{f}: {name}')
    except:
        pass
print('BROKEN' if broken else 'OK')
for b in broken:
    print(b)
"`

BLOCKER_IF:
  - Target entity file doesn't exist

DEPENDS_ON: none

---

## Execution Order
Serial: Contract #4 → Contract #5 → Contract #6 (can be parallelized by different worker instances)