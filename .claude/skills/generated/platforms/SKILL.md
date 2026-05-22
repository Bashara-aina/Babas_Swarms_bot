---
name: platforms
description: "Skill for the Platforms area of swarm-bot. 915 symbols across 117 files."
---

# Platforms

"915 symbols | 117 files | Cohesion: 60%"

## When to Use

- Working with code in `ext/`
- Understanding how guarded_call, load_registry, sync_agents_md work
- Modifying platforms-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/gateway/platforms/feishu.py` | _accounts_base_url, _post_registration, _init_registration, _begin_registration, _poll_registration (+115) |
| `ext/hermes-agent/gateway/platforms/yuanbao.py` | fetch, _extract_connect_id, _handle_frame, _extract_sender_key, _push_to_inbound (+53) |
| `ext/hermes-agent/gateway/platforms/telegram.py` | _telegram_ignored_threads, _should_process_message, send_image, disconnect, _escape_mdv2 (+47) |
| `ext/hermes-agent/gateway/platforms/discord.py` | on_ready, _run_post_connect_initialization, _get_discord_command_sync_policy, _resolve_allowed_usernames, _send_file_attachment (+44) |
| `ext/hermes-agent/gateway/platforms/weixin.py` | disconnect, send, _aes128_ecb_encrypt, _send_file, _outbound_media_builder (+43) |
| `ext/hermes-agent/gateway/platforms/base.py` | should_send_media_as_audio, stop_typing, send_voice, play_tts, send_video (+42) |
| `ext/hermes-agent/gateway/platforms/wecom.py` | send_image, connect, disconnect, _cleanup_ws, _open_connection (+38) |
| `ext/hermes-agent/gateway/platforms/api_server.py` | _check_auth, _check_jobs_available, _check_job_id, _handle_list_jobs, _handle_create_job (+38) |
| `ext/hermes-agent/gateway/platforms/matrix.py` | send_image, _is_duplicate_event, _is_self_sender, _is_system_or_bridge_sender, _on_room_message (+37) |
| `ext/hermes-agent/gateway/platforms/slack.py` | disconnect, _download_slack_file, _get_client, stop_typing, _resolve_user_name (+35) |

## Entry Points

Start here when exploring this area:

- **`guarded_call`** (Function) — `tools/skill_guardian.py:50`
- **`load_registry`** (Function) — `core/agent_registry.py:69`
- **`sync_agents_md`** (Function) — `core/wiki_manager.py:338`
- **`ruflo_health_monitor`** (Function) — `core/ruflo_manager.py:56`
- **`cleanup_screenshots`** (Function) — `core/tmp_cleanup.py:21`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `BasePlatformAdapter` | Class | `ext/hermes-agent/gateway/platforms/base.py` | 1205 |
| `ProgressCaptureAdapter` | Class | `ext/hermes-agent/tests/gateway/test_run_progress_topics.py` | 16 |
| `guarded_call` | Function | `tools/skill_guardian.py` | 50 |
| `load_registry` | Function | `core/agent_registry.py` | 69 |
| `sync_agents_md` | Function | `core/wiki_manager.py` | 338 |
| `ruflo_health_monitor` | Function | `core/ruflo_manager.py` | 56 |
| `cleanup_screenshots` | Function | `core/tmp_cleanup.py` | 21 |
| `test_write_and_read_file` | Function | `tests/test_vscode_bridge.py` | 18 |
| `load_agent_prompt` | Function | `ext/everything_claude_code/__init__.py` | 179 |
| `build_index` | Function | `core/integrations/second_brain_integration.py` | 54 |
| `kickoff` | Function | `core/integrations/crewai_orchestrator.py` | 79 |
| `warning` | Function | `core/observability/metrics.py` | 110 |
| `execute` | Function | `swarms_bot/orchestrator/nested_agents.py` | 59 |
| `register_from_config` | Function | `ext/hermes-agent/agent/shell_hooks.py` | 147 |
| `create_adapter` | Function | `ext/hermes-agent/gateway/platform_registry.py` | 159 |
| `discover_builtin_tools` | Function | `ext/hermes-agent/tools/registry.py` | 56 |
| `init_session` | Function | `ext/hermes-agent/tools/environments/base.py` | 329 |
| `on_ready` | Function | `ext/hermes-agent/gateway/platforms/discord.py` | 640 |
| `send_image` | Function | `ext/hermes-agent/gateway/platforms/wecom.py` | 1376 |
| `fetch` | Function | `ext/hermes-agent/gateway/platforms/yuanbao.py` | 731 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Run → Items` | cross_community | 8 |
| `Fetch → Items` | cross_community | 8 |
| `POST → Items` | cross_community | 8 |
| `POST → Items` | cross_community | 8 |
| `_ → Items` | cross_community | 8 |
| `GET → Items` | cross_community | 8 |
| `GET → Items` | cross_community | 8 |
| `GET → Items` | cross_community | 8 |
| `GET → Items` | cross_community | 8 |
| `GET → Items` | cross_community | 8 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Gateway | 154 calls |
| Tools | 59 calls |
| Hermes_cli | 47 calls |
| Honcho_plugin | 16 calls |
| Run_agent | 12 calls |
| Handlers | 7 calls |
| Test | 6 calls |
| Agent | 4 calls |

## How to Explore

1. `gitnexus_context({name: "guarded_call"})` — see callers and callees
2. `gitnexus_query({query: "platforms"})` — find related execution flows
3. Read key files listed above for implementation details
