---
name: computer-agent
description: "Skill for the Computer_agent area of swarm-bot. 45 symbols across 6 files."
---

# Computer_agent

45 symbols | 6 files | Cohesion: 74%

## When to Use

- Working with code in `computer_agent/`
- Understanding how detect_display, screenshot_region, get_screen_size work
- Modifying computer_agent-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `computer_agent/display.py` | _resolve_tool_bin, detect_display, _display_env, screenshot_region, get_screen_size (+24) |
| `computer_agent/tools.py` | _web_browse, _web_research, _web_get_links, _web_click, _doc_call (+5) |
| `computer_agent/shell.py` | install_packages, open_url, open_app |
| `tools/computer_use_agent.py` | _execute_action |
| `llm_client/__init__.py` | _execute_tool_with_self_heal |
| `handlers/computer.py` | cmd_open |

## Entry Points

Start here when exploring this area:

- **`detect_display`** (Function) — `computer_agent/display.py:34`
- **`screenshot_region`** (Function) — `computer_agent/display.py:172`
- **`get_screen_size`** (Function) — `computer_agent/display.py:184`
- **`mouse_click`** (Function) — `computer_agent/display.py:199`
- **`mouse_move`** (Function) — `computer_agent/display.py:217`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `detect_display` | Function | `computer_agent/display.py` | 34 |
| `screenshot_region` | Function | `computer_agent/display.py` | 172 |
| `get_screen_size` | Function | `computer_agent/display.py` | 184 |
| `mouse_click` | Function | `computer_agent/display.py` | 199 |
| `mouse_move` | Function | `computer_agent/display.py` | 217 |
| `mouse_drag` | Function | `computer_agent/display.py` | 227 |
| `scroll_at` | Function | `computer_agent/display.py` | 238 |
| `get_cursor_position` | Function | `computer_agent/display.py` | 254 |
| `keyboard_type` | Function | `computer_agent/display.py` | 271 |
| `key_press` | Function | `computer_agent/display.py` | 287 |
| `keyboard_shortcut` | Function | `computer_agent/display.py` | 301 |
| `list_windows` | Function | `computer_agent/display.py` | 306 |
| `focus_window` | Function | `computer_agent/display.py` | 319 |
| `get_active_window` | Function | `computer_agent/display.py` | 334 |
| `minimize_window` | Function | `computer_agent/display.py` | 348 |
| `maximize_window` | Function | `computer_agent/display.py` | 362 |
| `new_browser_tab` | Function | `computer_agent/display.py` | 389 |
| `switch_browser_tab` | Function | `computer_agent/display.py` | 409 |
| `close_browser_tab` | Function | `computer_agent/display.py` | 421 |
| `whatsapp_send_local` | Function | `computer_agent/display.py` | 475 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Computer_use_loop → Detect_display` | cross_community | 4 |
| `Execute_tool → Detect_display` | cross_community | 3 |
| `Execute_tool → _resolve_tool_bin` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Handlers | 2 calls |
| Tools | 2 calls |

## How to Explore

1. `gitnexus_context({name: "detect_display"})` — see callers and callees
2. `gitnexus_query({query: "computer_agent"})` — find related execution flows
3. Read key files listed above for implementation details
