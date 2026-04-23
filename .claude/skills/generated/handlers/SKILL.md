---
name: handlers
description: "Skill for the Handlers area of swarm-bot. 453 symbols across 107 files."
---

# Handlers

453 symbols | 107 files | Cohesion: 86%

## When to Use

- Working with code in `handlers/`
- Understanding how introspect_schema, generate_skill_file, query_natural work
- Modifying handlers-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `handlers/ecc_compat.py` | _extract_arg, cmd_harness_audit, cmd_model_route, _run_quality_gate, cmd_quality_gate (+41) |
| `handlers/system.py` | _ui_keyboard, _build_home_panel, _build_agents_panel, _build_audit_panel, _build_help_panel (+19) |
| `handlers/computer.py` | cmd_do, cmd_autopilot, on_progress, cmd_confirm, cmd_do_local (+14) |
| `handlers/ai.py` | _send_swarm_visualization, cmd_agent, cmd_swarm, cmd_owl, cmd_predict (+13) |
| `handlers/shared.py` | _format_for_telegram_html, is_allowed, allowed_cb, main_keyboard, result_keyboard (+9) |
| `handlers/harvest_review.py` | _build_candidate_card, _build_review_keyboard, _get_pending_candidates, _mark_reviewed, _load_harvest_stats (+8) |
| `handlers/gstack.py` | run_sync, escape, code, bold, cmd_review (+7) |
| `handlers/message_handler.py` | handle_plain_message, _handle_email, _handle_business, _handle_location, _handle_github_intel (+7) |
| `handlers/voice.py` | _voice_reply_enabled, _set_voice_reply_enabled, cmd_voice_on, cmd_voice_off, cmd_voice_status (+6) |
| `tools/quality_guard.py` | is_research_like, extract_urls, source_diversity, analyze_answer_consistency, estimate_confidence (+5) |

## Entry Points

Start here when exploring this area:

- **`introspect_schema`** (Function) — `tools/supabase_client.py:324`
- **`generate_skill_file`** (Function) — `tools/supabase_client.py:360`
- **`query_natural`** (Function) — `tools/supabase_client.py:403`
- **`health_check`** (Function) — `tools/supabase_client.py:483`
- **`is_configured`** (Function) — `tools/supabase_client.py:563`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `introspect_schema` | Function | `tools/supabase_client.py` | 324 |
| `generate_skill_file` | Function | `tools/supabase_client.py` | 360 |
| `query_natural` | Function | `tools/supabase_client.py` | 403 |
| `health_check` | Function | `tools/supabase_client.py` | 483 |
| `is_configured` | Function | `tools/supabase_client.py` | 563 |
| `list_skills` | Function | `tools/skill_loader.py` | 171 |
| `invalidate_cache` | Function | `tools/skill_loader.py` | 189 |
| `run_simulation` | Function | `tools/simulation_tool.py` | 10 |
| `add_monitor` | Function | `tools/scheduler.py` | 39 |
| `cancel` | Function | `tools/scheduler.py` | 92 |
| `list_tasks` | Function | `tools/scheduler.py` | 100 |
| `scaffold_fastapi` | Function | `tools/scaffolder.py` | 113 |
| `get_resource_snapshot` | Function | `tools/resource_monitor.py` | 194 |
| `can_use_local_model` | Function | `tools/resource_monitor.py` | 210 |
| `format_resource_html` | Function | `tools/resource_monitor.py` | 221 |
| `is_research_like` | Function | `tools/quality_guard.py` | 32 |
| `extract_urls` | Function | `tools/quality_guard.py` | 38 |
| `source_diversity` | Function | `tools/quality_guard.py` | 50 |
| `analyze_answer_consistency` | Function | `tools/quality_guard.py` | 73 |
| `estimate_confidence` | Function | `tools/quality_guard.py` | 94 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Handle_nl → Build_sensei_system_prompt` | cross_community | 4 |
| `Cmd_code_review → Escape` | intra_community | 4 |
| `Cmd_python_review → Escape` | intra_community | 4 |
| `Cmd_task_from → UpdateSendButton` | cross_community | 4 |
| `Handle_video → _find_server` | cross_community | 4 |
| `Handle_video → Initialize` | cross_community | 4 |
| `Handle_video → _tool_result_to_text` | cross_community | 4 |
| `Write_page → _result` | cross_community | 4 |
| `Handle_nl → Get_mastery_distribution` | cross_community | 3 |
| `Handle_nl → Get_phoneme_weaknesses` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 34 calls |
| Computer_agent | 6 calls |
| Llm_client | 5 calls |
| Tests | 5 calls |
| Bridges | 2 calls |
| Cluster_309 | 1 calls |
| Sessions | 1 calls |
| Daily_harvester | 1 calls |

## How to Explore

1. `gitnexus_context({name: "introspect_schema"})` — see callers and callees
2. `gitnexus_query({query: "handlers"})` — find related execution flows
3. Read key files listed above for implementation details
