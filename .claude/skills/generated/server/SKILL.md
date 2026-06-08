---
name: server
description: "Skill for the Server area of swarm-bot."
---

# Server

"server area"

## When to Use

- Working with code in `rustdesk/`
- Understanding how find_closest_lines, ratio, in_vbr_state work
- Modifying server-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `rustdesk/src/server/connection.rs` | try_sub_monitor_services, peer_keyboard_enabled, clipboard_enabled, can_sub_clipboard_service, file_transfer_enabled (+96) |
| `rustdesk/src/server/input_service.rs` | sleep_to_ensure_locked, wayland_use_uinput, wayland_use_rdp_input, send, run_window_focus (+64) |
| `rustdesk/src/server/portable_service.rs` | i32_to_vec, ptr_to_i32, counter_ready, counter_equal, increase_counter (+21) |
| `rustdesk/src/server/terminal_service.rs` | get_default_shell, is_service_specified_user, get_service, add_to_reaper, new (+19) |
| `rustdesk/src/server/video_qos.rs` | add_delay, avg_delay, ratio, in_vbr_state, user_image_quality (+15) |
| `rustdesk/src/server/video_service.rs` | set_take_screenshot, run, check_qos, handle_one_frame, get_capturer_monitor (+14) |
| `rustdesk/src/server.rs` | start_server, wait_initial_config_sync, sync_and_watch_config_dir, add_camera_connection, remove_connection (+13) |
| `rustdesk/src/server/display_service.rs` | set_last_changed_resolution, get_original_resolution, get_sync_displays, get_primary, get_primary_2 (+13) |
| `rustdesk/src/server/uinput.rs` | input_text_wayland, input_char_wayland_key_event, can_input_via_keysym, char_to_keysym, map_key (+12) |
| `rustdesk/src/server/audio_service.rs` | run, run_restart, run_serv_snapshot, play, create_format_msg (+6) |

## Entry Points

Start here when exploring this area:

- **`find_closest_lines`** (Function) — `ext/hermes-agent/tools/fuzzy_match.py:623`
- **`ratio`** (Function) — `rustdesk/src/server/video_qos.rs:158`
- **`in_vbr_state`** (Function) — `rustdesk/src/server/video_qos.rs:177`
- **`user_image_quality`** (Function) — `rustdesk/src/server/video_qos.rs:217`
- **`user_network_delay`** (Function) — `rustdesk/src/server/video_qos.rs:245`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `find_closest_lines` | Function | `ext/hermes-agent/tools/fuzzy_match.py` | 623 |
| `ratio` | Function | `rustdesk/src/server/video_qos.rs` | 158 |
| `in_vbr_state` | Function | `rustdesk/src/server/video_qos.rs` | 177 |
| `user_image_quality` | Function | `rustdesk/src/server/video_qos.rs` | 217 |
| `user_network_delay` | Function | `rustdesk/src/server/video_qos.rs` | 245 |
| `user_delay_response_elapsed` | Function | `rustdesk/src/server/video_qos.rs` | 335 |
| `update_display_data` | Function | `rustdesk/src/server/video_qos.rs` | 357 |
| `latest_quality` | Function | `rustdesk/src/server/video_qos.rs` | 403 |
| `can_input_via_keysym` | Function | `rustdesk/src/server/uinput.rs` | 504 |
| `char_to_keysym` | Function | `rustdesk/src/server/uinput.rs` | 510 |
| `map_key` | Function | `rustdesk/src/server/uinput.rs` | 552 |
| `is_service_specified_user` | Function | `rustdesk/src/server/terminal_service.rs` | 135 |
| `get_service` | Function | `rustdesk/src/server/terminal_service.rs` | 210 |
| `new` | Function | `rustdesk/src/server/terminal_service.rs` | 330 |
| `handle_action` | Function | `rustdesk/src/server/terminal_service.rs` | 861 |
| `read_outputs` | Function | `rustdesk/src/server/terminal_service.rs` | 1629 |
| `set_persistent` | Function | `rustdesk/src/server/terminal_service.rs` | 827 |
| `register_whiteboard` | Function | `rustdesk/src/whiteboard/client.rs` | 41 |
| `set_session_2fa` | Function | `rustdesk/src/server/connection.rs` | 5586 |
| `set_take_screenshot` | Function | `rustdesk/src/server/video_service.rs` | 1346 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Run → Is_x11` | cross_community | 9 |
| `Run → Items` | cross_community | 8 |
| `Run → Is_modifier_enabled` | cross_community | 7 |
| `Run → Is_legacy_mode` | cross_community | 7 |
| `Run → Should_disable_numlock` | cross_community | 7 |
| `Run → Get_hermes_home` | cross_community | 7 |
| `Start_os_service → Get_pid_file` | cross_community | 7 |
| `Start_os_service → CheckIfRestart` | cross_community | 7 |
| `Start_os_service → Strip` | cross_community | 6 |
| `Run → Is_server` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Platform | 44 calls |
| Tools | 33 calls |
| Plugin | 11 calls |
| Client | 8 calls |
| Hermes_cli | 8 calls |
| Hbbs_http | 6 calls |
| Scripts | 5 calls |
| Examples | 5 calls |

## How to Explore

1. `gitnexus_context({name: "find_closest_lines"})` — see callers and callees
2. `gitnexus_query({query: "server"})` — find related execution flows
3. Read key files listed above for implementation details
