---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/architecture/skill-execution-flow.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-10T01:00:00.502182"
}
---

---
title: Skill Execution Flow
type: architecture
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- architecture
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Skills execute through a dual-layer system: executable Python skills in
  `core/skills/` for direct actions (weather API calls, web search, timer execution),
  and reference markdown skills injected as...'
wikilinks: []
confidence: medium
source: research
---

# Skill Execution Flow

## TL;DR
Skills execute through a dual-layer system: executable Python skills in `core/skills/` for direct actions (weather API calls, web search, timer execution), and reference markdown skills injected as prompt context. The intent router triggers skills when confidence ≥ 0.7, the skill registry locates the appropriate handler, execution produces results that inject back into the LLM context for response synthesis.

## Skill Categories

### Category A: Reference Skills (28 markdown files)
- Located in `skills/` directory
- Injected into system prompts as context
- NOT executable — purely informational
- Examples: python-patterns, testing-patterns, debugging

### Category B: Executable Skills (`core/skills/`)
- Real Python async functions
- Can call APIs, run tools, query databases
- Registered in skill registry

## Dual-Layer Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     LLM Prompt Context                        │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ Reference       │  │ Skill Context  │  │ Other Layers  │  │
│  │ Skills (.md)    │  │ (executable)  │  │ (soul, etc.)  │  │
│  └────────────────┘  └────────────────┘  └───────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              ↑
                    Results injected here
                              │
┌──────────────────────────────────────────────────────────────┐
│                    Skill Executor                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Skill Registry (core/skills/registry.py)              │   │
│  │ - find_by_example() via keyword matching              │   │
│  │ - Skill metadata: name, triggers, timeout, fallback   │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                              ↑
                    Execution results
                              │
┌──────────────────────────────────────────────────────────────┐
│                    Skill Handlers                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐   │
│  │ weather │ │web_search│ │  timer  │ │ deep_research   │   │
│  │ (real)  │ │ (real)  │ │ (broken)│ │ (via gpt-       │   │
│  │  8/10   │ │  8/10   │ │  1/10   │ │  researcher)   │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Execution Flow

### Full Pipeline

```
1. User Message: "cek seo rumahlabuh"
       ↓
2. Intent Router (core/intent_router.py)
   - Keyword matching: "seo" → web_audit intent
   - Confidence: 0.85 (≥ 0.7 threshold)
       ↓
3. Skill Registry Lookup (core/skills/registry.py)
   - find_by_example("web_audit")
   - Returns: web_audit skill metadata
       ↓
4. API Key Check
   - skill.needs: ["GOOGLE_PAGESPEED_API_KEY"]
   - If missing: return fallback message
       ↓
5. Skill Execution (core/skills/web_audit.py)
   - asyncio timeout: 30s
   - Call Google PageSpeed API
   - Parse response
       ↓
6. Result Injection
   - PageSpeed score added to context
   - Passed to LLM as additional context
       ↓
7. LLM Response Generation
   - Synthesizes skill result + conversation
   - Returns natural language response
```

### Skill Registry Structure

```python
@dataclass
class Skill:
    name: str
    triggers: list[str]
    handler: Callable
    needs: list[str]  # API key names
    timeout: int
    fallback: str
    cost_tier: str  # "low", "medium", "high"
    avg_latency_seconds: int

SKILL_REGISTRY = {
    "weather": Skill(
        name="weather",
        triggers=["cuaca", "weather", "hujan"],
        handler=execute_weather,
        needs=["OPENWEATHERMAP_API_KEY"],
        timeout=10,
        fallback="Weather unavailable",
        cost_tier="low",
        avg_latency_seconds=2
    ),
    "web_search": Skill(
        name="web_search",
        triggers=["search", "cari", "google"],
        handler=execute_search,
        needs=["BRAVE_SEARCH_API_KEY"],
        timeout=15,
        fallback="Search unavailable",
        cost_tier="medium",
        avg_latency_seconds=5
    ),
    # ... 30+ skills total
}
```

## Executable Skills Inventory

| Skill | Quality | Status | Dependencies |
|-------|---------|--------|--------------|
| weather | 8/10 | Real | OpenWeatherMap API |
| web_search | 8/10 | Real | Brave Search API |
| github_pr_status | 8/10 | Real | GitHub token |
| hacker_news | 7/10 | Real | HN Firebase API |
| summarize_url | 6/10 | Partial | crawl4ai (may fail) |
| arxiv_search | 5/10 | Fragile | Regex XML parsing |
| translate | 4/10 | Weak | Hardcoded model, no retry |
| github_commits | 6/10 | Basic | GitHub token |
| timer | 1/10 | Fake | Does not actually set timer |
| code_review | 0/10 | Fake | Returns generic instructions |

## Swarm Wiring Integration

For `/swarm` command (from `wiki/raw/docs/swarm-wiring.md`):

```
/swarm <topic>
    ├─ Phase 1: Department Sprint (parallel)
    │   └─ 9 departments × 8 agents
    ├─ Phase 2: 4-Round Debate
    │   └─ 6 debate personas
    └─ Phase 3: Format → Telegram messages
```

Skills can be called within swarm agents:
- web_search skill during research phase
- code_review during engineering phase
- Weather/timer for practical department tasks

## Related Pages

- [[concepts/skill-registry]] — Skill management concepts
- [[architecture/legion-module-map]] — Module overview
- [[entities/gpt-researcher]] — Deep research integration
- [[entities/opencode]] — Code execution integration
