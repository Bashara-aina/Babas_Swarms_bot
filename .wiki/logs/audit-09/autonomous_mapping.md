# Autonomous Router Mapping — LEGION AUDIT 09
> Generated: 2026-04-12

## Manifest Skills → SKILL_PATTERNS Mapping

| Skill ID | Manifest Handler | SKILL_PATTERNS Key | SKILL_PATTERNS Handler | Match? | Notes |
|----------|------------------|---------------------|------------------------|--------|-------|
| `web_search` | `WebSearch` | **NONE** | — | ❌ | `deep_research` has overlapping keywords but different handler |
| `geo_intelligence` | `GeoIntelligence` | `location_advice` | `location` | ❌ | Keywords overlap (restaurant, hotel, nearby) but handler differs |
| `screenpipe_recall` | `screenpipe_tool` | **NONE** | — | ❌ | No screen context skill in SKILL_PATTERNS |
| `mirofish_simulation` | `mirofish` | `strategic_simulation` | `simulation` | ❌ | Handler differs ("simulation" vs "mirofish") but "mirofish" in keywords |
| `open_interpreter` | `interpreter_tool` | **NONE** | — | ❌ | No code execution skill in SKILL_PATTERNS |
| `database_agent` | `DatabaseAgent` | `business_query` | `business` | ❌ | Keywords overlap (supabase, database) but handler differs |

## SKILL_PATTERNS Keys (for reference)

```
computer_control, deep_research, code_generation, deep_reasoning, 
multi_agent_swarm, memory_search, system_control, email_management, 
runbook_maintenance, business_query, location_advice, whatsapp_action, 
github_intel, strategic_simulation, jarvis_orchestrate, codebase_understanding
```

## Wiring Gaps Analysis

| Gap | Manifest Skills | SKILL_PATTERNS | Issue |
|-----|-----------------|-----------------|-------|
| **Handler mismatch** | `WebSearch` | `deep_research` has handler `/research` | Handler strings don't match |
| **Handler mismatch** | `GeoIntelligence` | `location_advice` has handler `location` | Different naming convention |
| **No web_search entry** | `web_search` | No direct entry | Only `deep_research` with overlapping keywords |
| **No screen context** | `screenpipe_recall` | No entry | Screen context not in SKILL_PATTERNS |
| **No interpreter** | `open_interpreter` | No entry | Code execution not in SKILL_PATTERNS |
| **Handler mismatch** | `mirofish` | `strategic_simulation` handler is `simulation` | Different handler name |

## Root Cause

The manifest and SKILL_PATTERNS use different naming conventions:
- **Manifest**: Python class names (`WebSearch`, `GeoIntelligence`, `DatabaseAgent`)
- **SKILL_PATTERNS**: Lowercase action names (`location`, `business`, `simulation`)

These are not wired together — they appear to be two separate routing systems.

## Verdict

- ❌ **0/6 manifest skills have matching handler strings** in SKILL_PATTERNS
- ⚠️ **All 6 manifest skills have functional overlap** with SKILL_PATTERNS entries, but handler names don't align
- ⚠️ **3 skills have no SKILL_PATTERNS entry at all**: web_search, screenpipe_recall, open_interpreter
