---
name: platform
description: "Skill for the Platform area of swarm-bot. 297 symbols across 43 files."
---

# Platform

"297 symbols | 43 files | Cohesion: 59%"

## When to Use

- Working with code in `rustdesk/`
- Understanding how status, main, close_all_instances work
- Modifying platform-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `rustdesk/src/platform/windows.rs` | install_me, run_before_uninstall, write_cmds, get_undone_file, run_cmds (+89) |
| `rustdesk/src/platform/linux.rs` | get_pa_monitor, get_pa_source_name, get_pa_sources, get_envs, get_display_xauth_wayland (+45) |
| `rustdesk/src/platform/linux_desktop_manager.rs` | try_start_x_session, start_x_session, start_x_session_thread, stop_children, pam_get_service_name (+16) |
| `rustdesk/src/platform/macos.rs` | is_installed_daemon, update_daemon_agent, uninstall_service, get_active_user, get_active_username (+14) |
| `rustdesk/src/platform/windows.cc` | inputDesktopSelected, selectInputDesktop, get_di_bits, is_session_locked, flog (+7) |
| `rustdesk/src/common.rs` | check_software_update, is_custom_client, get_rendezvous_server, get_custom_rendezvous_server, get_api_server_ (+5) |
| `rustdesk/src/platform/win_device.rs` | new_api_last_err, setup_di_create_device_info_list, setup_di_get_class_devs_ex_w, install_driver, is_same_hardware_id (+4) |
| `rustdesk/src/platform/gtk_sudo.rs` | password_prompt, run, exec, cmd, cmd_parent (+4) |
| `rustdesk/src/virtual_display_manager.rs` | get_deviceinstaller64_work_dir, uninstall_driver, install_if_x86_on_x64, check_install_driver, plug_monitor_ (+2) |
| `rustdesk/src/ipc.rs` | close_all_instances, start_pa, next_timeout2, next, get_rendezvous_server |

## Entry Points

Start here when exploring this area:

- **`status`** (Function) — `core/memory/store.py:197`
- **`main`** (Function) — `core/memory/cli.py:11`
- **`close_all_instances`** (Function) — `rustdesk/src/ipc.rs:1522`
- **`success`** (Function) — `rustdesk/src/plugin/mod.rs:57`
- **`is_installed_daemon`** (Function) — `rustdesk/src/platform/macos.rs:188`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `status` | Function | `core/memory/store.py` | 197 |
| `main` | Function | `core/memory/cli.py` | 11 |
| `close_all_instances` | Function | `rustdesk/src/ipc.rs` | 1522 |
| `success` | Function | `rustdesk/src/plugin/mod.rs` | 57 |
| `is_installed_daemon` | Function | `rustdesk/src/platform/macos.rs` | 188 |
| `uninstall_service` | Function | `rustdesk/src/platform/macos.rs` | 314 |
| `get_active_username` | Function | `rustdesk/src/platform/macos.rs` | 653 |
| `get_active_userid` | Function | `rustdesk/src/platform/macos.rs` | 657 |
| `update_me` | Function | `rustdesk/src/platform/macos.rs` | 828 |
| `elevate` | Function | `rustdesk/src/platform/macos.rs` | 1155 |
| `on_texture` | Function | `rustdesk/src/flutter.rs` | 495 |
| `start_pa` | Function | `rustdesk/src/ipc.rs` | 943 |
| `next_timeout2` | Function | `rustdesk/src/ipc.rs` | 1097 |
| `next` | Function | `rustdesk/src/ipc.rs` | 1105 |
| `get_rendezvous_server` | Function | `rustdesk/src/ipc.rs` | 1354 |
| `get_sound_inputs` | Function | `rustdesk/src/ui_interface.rs` | 362 |
| `get_pa_monitor` | Function | `rustdesk/src/platform/linux.rs` | 1027 |
| `get_pa_source_name` | Function | `rustdesk/src/platform/linux.rs` | 1036 |
| `get_pa_sources` | Function | `rustdesk/src/platform/linux.rs` | 1045 |
| `on_printer_data` | Function | `rustdesk/src/server/connection.rs` | 5236 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Handle_msg_from_peer → Next` | cross_community | 7 |
| `Start_os_service → Get_pid_file` | cross_community | 7 |
| `Start_os_service → CheckIfRestart` | cross_community | 7 |
| `Run → CustomServer` | cross_community | 7 |
| `Run → Get_custom_server_from_config_string` | cross_community | 7 |
| `Start_os_service → Strip` | cross_community | 6 |
| `Main → Wide_string` | cross_community | 5 |
| `Start_os_service → Next` | cross_community | 5 |
| `Handle_msg_from_peer → Is_view_camera` | cross_community | 4 |
| `Start → DelegateState` | intra_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 17 calls |
| Server | 13 calls |
| Plugin | 12 calls |
| Linux | 5 calls |
| Client | 4 calls |
| Handlers | 4 calls |
| Hermes_cli | 3 calls |
| Ui | 3 calls |

## How to Explore

1. `gitnexus_context({name: "status"})` — see callers and callees
2. `gitnexus_query({query: "platform"})` — find related execution flows
3. Read key files listed above for implementation details
