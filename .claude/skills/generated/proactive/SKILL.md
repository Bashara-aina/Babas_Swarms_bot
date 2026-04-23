---
name: proactive
description: "Skill for the Proactive area of swarm-bot. 65 symbols across 13 files."
---

# Proactive

65 symbols | 13 files | Cohesion: 85%

## When to Use

- Working with code in `core/`
- Understanding how check_website_uptime, start_proactive_initiator, get_quick_brief work
- Modifying proactive-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `core/proactive/curiosity_engine.py` | _today_str, reset_if_new_day, can_send, record_send, _check_site_health (+8) |
| `core/proactive/scheduler.py` | _jst_now, start, _loop, _run_checks, _check_rumahlabuh_30min (+7) |
| `core/soul_engine.py` | get_emotional_state, _jst_now, get_cached_soul, read_soul, get_pending_followups (+4) |
| `core/proactive/proactive_initiator.py` | _can_send, _mark_sent, _check_gpu_temp, _check_ram, _check_disk (+4) |
| `core/memory/episodic_store.py` | recall, _supabase_recall, _local_recall, get_upcoming_schedule, get_episodic_store |
| `core/self_upgrade.py` | scan_github_trending, _fetch_trending_repos, format_evaluations_for_telegram, scan_weekly_trends, _notify |
| `tools/proactive_initiator.py` | _is_quiet_hours, _pick_trigger, _build_message, start_proactive_initiator |
| `tools/briefing.py` | _get_weather, get_quick_brief |
| `tools/proactive_monitors.py` | get_snapshot, monitor_loop |
| `tools/rumahlabuh_crew.py` | check_website_uptime |

## Entry Points

Start here when exploring this area:

- **`check_website_uptime`** (Function) — `tools/rumahlabuh_crew.py:86`
- **`start_proactive_initiator`** (Function) — `tools/proactive_initiator.py:187`
- **`get_quick_brief`** (Function) — `tools/briefing.py:302`
- **`get_emotional_state`** (Function) — `core/soul_engine.py:289`
- **`start`** (Function) — `core/proactive/scheduler.py:52`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `check_website_uptime` | Function | `tools/rumahlabuh_crew.py` | 86 |
| `start_proactive_initiator` | Function | `tools/proactive_initiator.py` | 187 |
| `get_quick_brief` | Function | `tools/briefing.py` | 302 |
| `get_emotional_state` | Function | `core/soul_engine.py` | 289 |
| `start` | Function | `core/proactive/scheduler.py` | 52 |
| `recall` | Function | `core/memory/episodic_store.py` | 192 |
| `get_upcoming_schedule` | Function | `core/memory/episodic_store.py` | 237 |
| `get_episodic_store` | Function | `core/memory/episodic_store.py` | 518 |
| `get_snapshot` | Function | `tools/proactive_monitors.py` | 25 |
| `monitor_loop` | Function | `tools/proactive_monitors.py` | 54 |
| `check_triggers` | Function | `core/proactive/proactive_initiator.py` | 182 |
| `format_health_for_prompt` | Function | `tools/browser_agent.py` | 364 |
| `reset_if_new_day` | Function | `core/proactive/curiosity_engine.py` | 88 |
| `can_send` | Function | `core/proactive/curiosity_engine.py` | 94 |
| `record_send` | Function | `core/proactive/curiosity_engine.py` | 98 |
| `run_curiosity_loop` | Function | `core/proactive/curiosity_engine.py` | 181 |
| `get_cached_soul` | Function | `core/soul_engine.py` | 82 |
| `read_soul` | Function | `core/soul_engine.py` | 97 |
| `get_pending_followups` | Function | `core/soul_engine.py` | 246 |
| `get_time_context` | Function | `core/soul_engine.py` | 268 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `On_startup → Format_health_for_prompt` | cross_community | 7 |
| `On_startup → Can_send_sleep_checkin` | cross_community | 7 |
| `On_startup → _jst_hour` | cross_community | 7 |
| `On_startup → Record_sleep_checkin` | cross_community | 7 |
| `Build_enhanced_soul_context → Read_soul` | intra_community | 3 |
| `Build_enhanced_soul_context → Read_beliefs` | cross_community | 3 |
| `Build_enhanced_soul_context → _jst_now` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 2 calls |
| Reflection | 2 calls |
| Handlers | 1 calls |
| Cluster_311 | 1 calls |
| Scripts | 1 calls |
| Tests | 1 calls |
| Memory | 1 calls |

## How to Explore

1. `gitnexus_context({name: "check_website_uptime"})` — see callers and callees
2. `gitnexus_query({query: "proactive"})` — find related execution flows
3. Read key files listed above for implementation details
