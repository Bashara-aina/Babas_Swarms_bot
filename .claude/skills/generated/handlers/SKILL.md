---
name: handlers
description: "Skill for the Handlers area of swarm-bot. 374 symbols across 100 files."
---

# Handlers

"374 symbols | 100 files | Cohesion: 68%"

## When to Use

- Working with code in `handlers/`
- Understanding how start_sidecar, get_status, get_unread work
- Modifying handlers-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `handlers/ecc_compat.py` | cmd_harness_audit, cmd_model_route, _run_quality_gate, cmd_quality_gate, cmd_verify (+38) |
| `handlers/system.py` | _build_audit_panel, cb_cmd_redirect, cb_ui_panel, _build_visual_summary, cmd_visualize (+20) |
| `handlers/computer.py` | cmd_do, cmd_autopilot, cmd_confirm, cmd_do_local, cmd_open (+11) |
| `handlers/ai.py` | _send_swarm_visualization, cmd_swarm, cmd_owl, cmd_predict, cmd_code_exec (+7) |
| `handlers/gstack.py` | escape, cmd_review, run_opencode_cmd, code, bold (+6) |
| `handlers/legiona_tools.py` | _route_via_intent, cmd_ps, cmd_kill, cmd_ls, cmd_find (+6) |
| `handlers/shared.py` | is_allowed, allowed_cb, send_chunked, _keep_typing, _key_status (+5) |
| `handlers/harvest_review.py` | _build_candidate_card, _get_pending_candidates, _mark_reviewed, _write_feedback_to_log, _update_scorer_bias (+5) |
| `handlers/voice.py` | _transcribe, _reply_with_optional_tts, handle_voice, handle_audio, _voice_reply_enabled (+5) |
| `handlers/message_handler.py` | _handle_email, _handle_business, _handle_github_intel, _handle_codebase_understanding, _wa_is_intent_message (+4) |

## Entry Points

Start here when exploring this area:

- **`start_sidecar`** (Function) — `bridges/whatsapp_bridge.py:43`
- **`get_status`** (Function) — `bridges/whatsapp_bridge.py:97`
- **`get_unread`** (Function) — `bridges/whatsapp_bridge.py:128`
- **`run_shell_command`** (Function) — `llm_client/__init__.py:2662`
- **`add_instinct`** (Function) — `tools/persistence.py:404`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `start_sidecar` | Function | `bridges/whatsapp_bridge.py` | 43 |
| `get_status` | Function | `bridges/whatsapp_bridge.py` | 97 |
| `get_unread` | Function | `bridges/whatsapp_bridge.py` | 128 |
| `run_shell_command` | Function | `llm_client/__init__.py` | 2662 |
| `add_instinct` | Function | `tools/persistence.py` | 404 |
| `analyze_answer_consistency` | Function | `tools/quality_guard.py` | 73 |
| `build_evidence_envelope` | Function | `tools/quality_guard.py` | 108 |
| `stop_loop` | Function | `tools/autonomous_loop.py` | 70 |
| `get_pending_confirmations` | Function | `tools/computer_use_agent.py` | 101 |
| `fetch_readme` | Function | `tools/github_intel.py` | 131 |
| `generate_intel_report` | Function | `tools/github_intel.py` | 218 |
| `is_openclaw_running` | Function | `tools/openclaw_bridge.py` | 27 |
| `run_tests` | Function | `tools/dev_tools.py` | 18 |
| `query_natural` | Function | `tools/supabase_client.py` | 406 |
| `health_check` | Function | `tools/supabase_client.py` | 487 |
| `is_configured` | Function | `tools/supabase_client.py` | 567 |
| `render_suite_report_html` | Function | `tools/capability_benchmark.py` | 158 |
| `get_resource_snapshot` | Function | `tools/resource_monitor.py` | 194 |
| `format_resource_html` | Function | `tools/resource_monitor.py` | 221 |
| `review_code` | Function | `tools/code_reviewer.py` | 65 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Start_os_service → Strip` | cross_community | 6 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 74 calls |
| Platforms | 11 calls |
| Llm_client | 6 calls |
| Memory | 5 calls |
| Session | 4 calls |
| Cluster_185 | 3 calls |
| Computer_agent | 3 calls |
| Cluster_168 | 2 calls |

## How to Explore

1. `gitnexus_context({name: "start_sidecar"})` — see callers and callees
2. `gitnexus_query({query: "handlers"})` — find related execution flows
3. Read key files listed above for implementation details
