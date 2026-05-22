---
name: plugins
description: "Skill for the Plugins area of swarm-bot. 138 symbols across 24 files."
---

# Plugins

"138 symbols | 24 files | Cohesion: 73%"

## When to Use

- Working with code in `ext/`
- Understanding how test_system_prompt_block, test_handle_tool_call_unknown_tool, test_dispatch_profile work
- Modifying plugins-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/tests/plugins/test_disk_cleanup_plugin.py` | _load_plugin_init, test_help, test_status_empty, test_track_rejects_missing, test_track_rejects_bad_category (+28) |
| `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | test_system_prompt_block, test_handle_tool_call_unknown_tool, test_dispatch_profile, test_dispatch_search_requires_query, test_dispatch_search (+22) |
| `ext/hermes-agent/tests/plugins/test_google_meet_node.py` | test_server_handle_request_rejects_bad_token, test_server_handle_request_ping, test_server_handle_request_status_dispatches_to_pm, test_server_handle_request_start_bot_dispatches, test_server_handle_request_start_bot_missing_url (+14) |
| `ext/hermes-agent/plugins/google_meet/cli.py` | meet_command, _cmd_say, _cmd_status, _cmd_transcript, register_cli |
| `ext/hermes-agent/plugins/google_meet/node/client.py` | _rpc, stop, status, transcript, say |
| `ext/hermes-agent/web/src/plugins/registry.ts` | getPluginComponent, onPluginRegistered, _notify, notifyPluginRegistry, setPluginLoadError |
| `ext/hermes-agent/tests/plugins/test_google_meet_realtime.py` | _install_fake_websockets, test_speak_sends_create_and_response_and_writes_audio, test_close_is_idempotent_and_closes_ws, test_connect_sends_session_update_with_voice_and_instructions, test_speak_raises_on_error_frame |
| `ext/hermes-agent/plugins/memory/retaindb/__init__.py` | initialize, handle_tool_call, enqueue, on_memory_write |
| `ext/hermes-agent/plugins/google_meet/node/server.py` | ensure_token, get_token, _handle_request, _handler |
| `ext/hermes-agent/plugins/disk-cleanup/disk_cleanup.py` | dry_run, track, guess_category, is_safe_path |

## Entry Points

Start here when exploring this area:

- **`test_system_prompt_block`** (Function) — `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py:390`
- **`test_handle_tool_call_unknown_tool`** (Function) — `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py:404`
- **`test_dispatch_profile`** (Function) — `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py:411`
- **`test_dispatch_search_requires_query`** (Function) — `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py:419`
- **`test_dispatch_search`** (Function) — `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py:426`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_system_prompt_block` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 390 |
| `test_handle_tool_call_unknown_tool` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 404 |
| `test_dispatch_profile` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 411 |
| `test_dispatch_search_requires_query` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 419 |
| `test_dispatch_search` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 426 |
| `test_dispatch_search_top_k_capped` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 434 |
| `test_dispatch_remember` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 444 |
| `test_dispatch_remember_requires_content` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 452 |
| `test_dispatch_forget` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 459 |
| `test_dispatch_forget_requires_id` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 467 |
| `test_dispatch_context` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 474 |
| `test_dispatch_file_list` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 484 |
| `test_dispatch_file_upload_missing_path` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 492 |
| `test_dispatch_file_upload_not_found` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 498 |
| `test_dispatch_file_read_requires_id` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 505 |
| `test_dispatch_file_ingest_requires_id` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 512 |
| `test_dispatch_file_delete_requires_id` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 519 |
| `test_handle_tool_call_wraps_exception` | Function | `ext/hermes-agent/tests/plugins/test_retaindb_plugin.py` | 526 |
| `initialize` | Function | `ext/hermes-agent/plugins/memory/retaindb/__init__.py` | 488 |
| `handle_tool_call` | Function | `ext/hermes-agent/plugins/memory/retaindb/__init__.py` | 650 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Disk-cleanup | 11 calls |
| Google_meet | 9 calls |
| Session | 4 calls |
| Honcho_plugin | 3 calls |
| Run_agent | 3 calls |
| Dashboard | 3 calls |
| Gateway | 2 calls |
| Node | 2 calls |

## How to Explore

1. `gitnexus_context({name: "test_system_prompt_block"})` — see callers and callees
2. `gitnexus_query({query: "plugins"})` — find related execution flows
3. Read key files listed above for implementation details
