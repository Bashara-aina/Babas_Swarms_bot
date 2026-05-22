---
name: plugin
description: "Skill for the Plugin area of swarm-bot. 124 symbols across 22 files."
---

# Plugin

"124 symbols | 22 files | Cohesion: 63%"

## When to Use

- Working with code in `rustdesk/`
- Understanding how start, new, connect work
- Modifying plugin-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `rustdesk/src/ipc.rs` | start, new, handle, connect, send (+29) |
| `rustdesk/src/plugin/manager.rs` | install_plugin, uninstall_plugin, send_install_status, download_to_file, download_file (+16) |
| `rustdesk/src/plugin/plugins.rs` | load_plugin_path, sync_ui, reload_ui, _handle_listen_event, handle_listen_event (+11) |
| `rustdesk/src/plugin/mod.rs` | is_success, get_code_msg, free_c_ptr, str_to_cstr_ret, cstr_to_string (+5) |
| `rustdesk/src/plugin/config.rs` | path_plugins, path, set_plugin_option_enabled, add_plugin, load (+4) |
| `rustdesk/src/plugin/ipc.rs` | get_config, get_config_async, get_manager_config_async, handle_plugin, get_manager_plugin_config (+1) |
| `rustdesk/src/plugin/callback_msg.rs` | is_peer_channel, push_event_to_ui, push_option_to_ui, cb_msg, handle_msg_to_rustdesk (+1) |
| `rustdesk/src/flutter_ffi.rs` | main_broadcast_message, plugin_sync_ui, plugin_install, plugin_is_enabled |
| `rustdesk/src/platform/windows.rs` | try_remove_temp_update_files, run_uac, elevate |
| `rustdesk/src/ui_interface.rs` | change_id_shared_, check_hwcodec |

## Entry Points

Start here when exploring this area:

- **`start`** (Function) — `rustdesk/src/ipc.rs:397`
- **`new`** (Function) — `rustdesk/src/ipc.rs:472`
- **`connect`** (Function) — `rustdesk/src/ipc.rs:935`
- **`send`** (Function) — `rustdesk/src/ipc.rs:1082`
- **`next_timeout`** (Function) — `rustdesk/src/ipc.rs:1093`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `start` | Function | `rustdesk/src/ipc.rs` | 397 |
| `new` | Function | `rustdesk/src/ipc.rs` | 472 |
| `connect` | Function | `rustdesk/src/ipc.rs` | 935 |
| `send` | Function | `rustdesk/src/ipc.rs` | 1082 |
| `next_timeout` | Function | `rustdesk/src/ipc.rs` | 1093 |
| `set_config_async` | Function | `rustdesk/src/ipc.rs` | 1153 |
| `get_options_async` | Function | `rustdesk/src/ipc.rs` | 1379 |
| `get_options` | Function | `rustdesk/src/ipc.rs` | 1384 |
| `set_option` | Function | `rustdesk/src/ipc.rs` | 1396 |
| `set_options` | Function | `rustdesk/src/ipc.rs` | 1407 |
| `get_rendezvous_servers` | Function | `rustdesk/src/ipc.rs` | 1436 |
| `set_socks` | Function | `rustdesk/src/ipc.rs` | 1465 |
| `test_rendezvous_server` | Function | `rustdesk/src/ipc.rs` | 1506 |
| `send_url_scheme` | Function | `rustdesk/src/ipc.rs` | 1513 |
| `connect_to_user_session` | Function | `rustdesk/src/ipc.rs` | 1530 |
| `notify_server_to_check_hwcodec` | Function | `rustdesk/src/ipc.rs` | 1537 |
| `get_port_forward_session_count` | Function | `rustdesk/src/ipc.rs` | 1543 |
| `get_hwcodec_config_from_server` | Function | `rustdesk/src/ipc.rs` | 1555 |
| `client_get_hwcodec_config_thread` | Function | `rustdesk/src/ipc.rs` | 1577 |
| `hwcodec_process` | Function | `rustdesk/src/ipc.rs` | 1603 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Handle_msg_from_peer → CheckIfRestart` | cross_community | 8 |
| `Handle_msg_from_peer → Next` | cross_community | 7 |
| `Start_os_service → CheckIfRestart` | cross_community | 7 |
| `Handle_msg_from_peer → Send` | cross_community | 6 |
| `Main → Send` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Platform | 13 calls |
| Server | 8 calls |
| Native_handlers | 6 calls |
| Cluster_579 | 3 calls |
| Cluster_663 | 3 calls |
| Tools | 2 calls |
| Get_socks | 2 calls |
| Scripts | 2 calls |

## How to Explore

1. `gitnexus_context({name: "start"})` — see callers and callees
2. `gitnexus_query({query: "plugin"})` — find related execution flows
3. Read key files listed above for implementation details
