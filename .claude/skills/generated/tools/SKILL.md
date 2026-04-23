---
name: tools
description: "Skill for the Tools area of swarm-bot. 681 symbols across 160 files."
---

# Tools

681 symbols | 160 files | Cohesion: 83%

## When to Use

- Working with code in `tools/`
- Understanding how save_tasks_local, complete_task, add_scheduled_task work
- Modifying tools-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tools/rumahlabuh_thread_generator.py` | _safe_choice, _normalize, _render_template, _signature, get_price_min (+28) |
| `tools/memory.py` | _init_db, get_recent, delete_memory, count_memories, export_to_obsidian (+18) |
| `core/tools/computer_control.py` | _import_deps, _ensure_gui_available, _check_action_limit, find_element, click_element (+14) |
| `tools/persistence.py` | add_scheduled_task, update_task_status, update_task_last_run, record_task_execution, store_conversation (+12) |
| `tools/composio_client.py` | is_available, gmail_send, gmail_search, calendar_list_upcoming, calendar_create_event (+10) |
| `main.py` | _run_group_a_startup, _start_observability, _start_registry, _start_n8n, _start_monitors (+9) |
| `tools/supabase_client.py` | _rest_url, _headers, _raise_for_status_with_detail, _build_filters, query (+9) |
| `tools/orchestrator.py` | _is_research_like, _extract_urls, _estimate_confidence, _evidence_envelope, _verify_final_output (+8) |
| `core/task_router.py` | route, _run_research, _run_code, _run_document, one (+7) |
| `tools/memoryos_client.py` | _try_init_external, get_memoryos, mos_add_conversation, mos_retrieve_context, mos_get_stats (+6) |

## Entry Points

Start here when exploring this area:

- **`save_tasks_local`** (Function) — `tools/project_manager.py:52`
- **`complete_task`** (Function) — `tools/project_manager.py:126`
- **`add_scheduled_task`** (Function) — `tools/persistence.py:124`
- **`update_task_status`** (Function) — `tools/persistence.py:157`
- **`update_task_last_run`** (Function) — `tools/persistence.py:167`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `save_tasks_local` | Function | `tools/project_manager.py` | 52 |
| `complete_task` | Function | `tools/project_manager.py` | 126 |
| `add_scheduled_task` | Function | `tools/persistence.py` | 124 |
| `update_task_status` | Function | `tools/persistence.py` | 157 |
| `update_task_last_run` | Function | `tools/persistence.py` | 167 |
| `record_task_execution` | Function | `tools/persistence.py` | 178 |
| `store_conversation` | Function | `tools/persistence.py` | 212 |
| `kv_set` | Function | `tools/persistence.py` | 254 |
| `kv_delete` | Function | `tools/persistence.py` | 274 |
| `log_audit` | Function | `tools/persistence.py` | 284 |
| `save_session` | Function | `tools/persistence.py` | 337 |
| `delete_session` | Function | `tools/persistence.py` | 388 |
| `bump_instinct_use` | Function | `tools/persistence.py` | 430 |
| `delete_instinct` | Function | `tools/persistence.py` | 440 |
| `cache_set` | Function | `tools/persistence.py` | 485 |
| `cache_cleanup` | Function | `tools/persistence.py` | 524 |
| `cmd_task_done` | Function | `handlers/pm.py` | 74 |
| `delete` | Function | `core/persistent_loop.py` | 81 |
| `publish` | Function | `swarms_bot/orchestrator/agent_messaging.py` | 73 |
| `log` | Function | `swarms_bot/audit/audit_logger.py` | 107 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → UpdateSendButton` | cross_community | 8 |
| `On_startup → Format_health_for_prompt` | cross_community | 7 |
| `On_startup → Can_send_sleep_checkin` | cross_community | 7 |
| `On_startup → _jst_hour` | cross_community | 7 |
| `On_startup → Record_sleep_checkin` | cross_community | 7 |
| `Generate_report → UpdateSendButton` | cross_community | 7 |
| `Chat_with_report_agent → UpdateSendButton` | cross_community | 7 |
| `Prepare_simulation → UpdateSendButton` | cross_community | 6 |
| `Start_simulation → UpdateSendButton` | cross_community | 6 |
| `Get_prepare_status → UpdateSendButton` | cross_community | 6 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Handlers | 38 calls |
| Tests | 18 calls |
| Llm_client | 10 calls |
| Memory | 8 calls |
| Services | 8 calls |
| Bridges | 4 calls |
| Proactive | 3 calls |
| Computer_agent | 3 calls |

## How to Explore

1. `gitnexus_context({name: "save_tasks_local"})` — see callers and callees
2. `gitnexus_query({query: "tools"})` — find related execution flows
3. Read key files listed above for implementation details
