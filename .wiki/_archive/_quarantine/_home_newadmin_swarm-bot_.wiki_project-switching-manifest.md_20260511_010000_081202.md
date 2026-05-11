---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/project-switching-manifest.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-11T01:00:00.081223"
}
---

---
title: Project Switching Manifest
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# PROJECT SWITCHING MANIFEST
# ===========================
# Legion works on 3 projects. This file documents the active projects,
# their locations, and how to switch between them.
# Read by: Legion at session boot or when project switch is detected.
# Updated: 2026-05-03

## ACTIVE PROJECTS

| Project | Path | Type | Primary Agents | Key MCPs |
|---------|------|------|--------------|-----------|
| swarm-bot | /home/newadmin/swarm-bot | Telegram bot, AI agent OS | legiona/, hermes-agent, deployment-engineer | hermes, gitnexus, ruflo, filesystem, obsidian |
| cekwajar | /home/newadmin/cekwajar.id | Next.js SaaS (Indonesian finance tools) | frontend/, backend/, db/ | gitnexus, filesystem, git, exa |
| popw | /home/newadmin/swarm-bot/project/popw | Research, academic writing | paper-wiki-writer, research-agent, hermes-researcher | exa, crawl4ai, obsidian, latex |

## SWITCHING DETECTION

Legion detects project switch from:
1. `cwd` — current working directory
2. First message context — keywords like "cekwajar", "popw", "swarm-bot"
3. Files being referenced — paths containing project identifiers

## SWITCH PROTOCOL

When switching projects, execute this sequence silently:

```
1. [WRITE] Current project session summary → hermes write_skill + /tmp/legion_session_summary.txt
2. [READ] hermes_search_memory("[new project] recent state decisions")
3. [READ] git log --oneline -10 && git status (in new project directory)
4. [LOAD] Relevant domain agents for new project
5. [ANNOUNCE] "Switching to [project]. Last I knew: [2-sentence state summary]."
```

## PROJECT DETAILS

### swarm-bot
- **Location**: /home/newadmin/swarm-bot
- **Type**: Telegram bot + multi-agent AI OS
- **Stack**: Python, aiogram 3.4+, litellm, mem0ai, SQLite
- **Key files**: main.py, core/soul_engine.py, core/intent_router.py, agents.py
- **LLM**: MiniMax M2.7 via LiteLLM proxy (localhost:4000)
- **Memory**: mem0ai (semantic) + aiosqlite (episodic)
- **Bot token**: TELEGRAM_BOT_TOKEN env var
- **Known issues**: None active

### cekwajar
- **Location**: /home/newadmin/cekwajar.id
- **Type**: Next.js SaaS (5 Indonesian financial transparency tools)
- **Stack**: Next.js 15.1, React 19, TypeScript 5.7, Tailwind 3.4, Supabase
- **Key routes**:
  - /wajar-slip (payslip OCR + PPh21 audit)
  - /wajar-gaji (salary benchmark)
  - /wajar-tanah (land price fairness)
  - /wajar-kabur (migration score)
  - /wajar-hidup (cost of living)
- **DB**: Supabase (postgres)
- **Anti-slop UI**: magicui + motion-primitives + tremor + cult-ui
- **Model**: MiniMax M2.7 for all LLM, Supabase for data

### popw
- **Location**: /home/newadmin/swarm-bot/project/popw
- **Type**: Research project, academic writing
- **Stack**: LaTeX, Python (PyTorch), academic papers
- **Focus**: Multi-task learning, pose estimation, Mamba architectures
- **Key MCPs**: exa (research), crawl4ai (paper extraction), latex (document editing)
- **Output**: Academic papers, research notes in .wiki/popw-references/

## LAST KNOWN STATE (2026-05-03)

### swarm-bot
- Legion v11 cognitive OS being integrated
- 12/12 MCP servers live
- mem0ai working (imports as `from mem0 import Memory`)
- 15 agent files defined in .opencode/agents/
- Wiki: 3795 files, 205 uncommitted changes

### cekwajar
- Next.js 15.1 + React 19 deployed
- 5 tools in various states of completion
- UI stack: anti-slop repos integrated (magicui, motion-primitives, tremor, cult-ui)

### popw
- Research on Mamba, pose estimation, Kendall uncertainty weighting
- Academic paper writing in progress
- LaTeX MCP server available for document editing

## HEALTH CHECK COMMANDS

```bash
# swarm-bot
cd /home/newadmin/swarm-bot
python3 -c "from core.soul_engine import build_soul_context; print(build_soul_context()[:100])"
curl http://localhost:4000/health  # LiteLLM

# cekwajar
cd /home/newadmin/cekwajar.id
npm run typecheck
git status

# popw
cd /home/newadmin/swarm-bot/project/popw
latex_latex_health  # via MCP
```
