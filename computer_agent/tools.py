"""computer_agent/tools.py — Tool definitions and executor dispatcher for LLM function calling."""

from __future__ import annotations

from typing import Any


async def _web_browse(args: dict) -> str:
    from tools.web_browser import browse_url

    result = await browse_url(
        args["url"],
        extract_selector=args.get("extract_selector", "body"),
    )
    text = result.get("text", "")
    title = result.get("title", "")
    url = result.get("url", "")
    links_count = len(result.get("links", []))
    return f"Title: {title}\nURL: {url}\nLinks found: {links_count}\n\n{text}"


async def _web_search(args: dict) -> str:
    from tools.web_browser import web_search

    results = await web_search(
        args["query"],
        num_results=args.get("num_results", 10),
    )
    if not results:
        return "No search results found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('title', '(no title)')}")
        lines.append(f"    {r.get('url', '')}")
        snippet = r.get("snippet", "")
        if snippet:
            lines.append(f"    {snippet[:150]}")
        lines.append("")
    return "\n".join(lines)


async def _web_research(args: dict) -> str:
    from tools.web_browser import deep_research

    return await deep_research(
        args["topic"],
        max_pages=args.get("max_pages", 10),
    )


async def _web_fill_form(args: dict) -> str:
    from tools.web_browser import fill_form

    return await fill_form(
        args["url"],
        args.get("fields", {}),
        submit=args.get("submit", False),
    )


async def _web_get_links(args: dict) -> str:
    from tools.web_browser import get_page_links

    links = await get_page_links(
        args["url"],
        filter_pattern=args.get("filter_pattern", ""),
    )
    if not links:
        return "No links found."
    lines = [f"[{i + 1}] {l.get('text', '(no text)')[:60]} → {l.get('href', '')}" for i, l in enumerate(links)]
    return "\n".join(lines)


async def _web_click(args: dict) -> str:
    from tools.web_browser import browse_and_click

    result = await browse_and_click(args["url"], args["click_text"])
    text = result.get("text", "")
    title = result.get("title", "")
    return f"After click — Title: {title}\nURL: {result.get('url', '')}\n\n{text}"


async def _doc_call(func_name: str, args: dict) -> str:
    from tools import documents

    fn = getattr(documents, func_name)
    kwargs = {k: v for k, v in args.items() if v is not None}
    return await fn(**kwargs)


async def _email_call(func_name: str, args: dict) -> str:
    from tools import email_client

    fn = getattr(email_client, func_name)
    kwargs = {k: v for k, v in args.items() if v is not None}
    return await fn(**kwargs)


async def _git_call(func_name: str, args: dict) -> str:
    from tools import git_tools

    fn = getattr(git_tools, func_name)
    kwargs = {k: v for k, v in args.items() if v is not None}
    return await fn(**kwargs)


async def _dev_call(func_name: str, args: dict) -> str:
    from tools import dev_tools

    fn = getattr(dev_tools, func_name)
    kwargs = {k: v for k, v in args.items() if v is not None}
    return await fn(**kwargs)


async def _maint_call(func_name: str, args: dict) -> str:
    from tools import system_maintenance

    fn = getattr(system_maintenance, func_name)
    kwargs = {k: v for k, v in args.items() if v is not None}
    return await fn(**kwargs)


TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "shell_execute",
            "description": (
                "Execute any bash/shell command on Bas's Linux PC. "
                "Use for: checking files, running scripts, git operations, "
                "system status, process management, installing software, anything CLI. "
                "Always use this when the user says 'cek', 'check', 'lihat', 'show me' "
                "something on the computer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Full bash command to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Max seconds to wait (default 30)"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": (
                "Take a screenshot of the current desktop. "
                "Call this to SEE what's on screen before clicking or interacting with UI. "
                "The image will be sent to Bas in Telegram automatically."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": (
                "Click at (x, y) pixel coordinates on screen. "
                "ALWAYS take a screenshot first to determine the correct coordinates."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Horizontal pixels from left"},
                    "y": {"type": "integer", "description": "Vertical pixels from top"},
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "double"],
                        "description": "Click type (default: left)"
                    }
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_type",
            "description": (
                "Type text using the keyboard. Use after clicking a text input field. "
                "For passwords or sensitive data, the user should type manually."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                    "delay_ms": {
                        "type": "integer",
                        "description": "Delay between keystrokes ms (default 30)"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "key_press",
            "description": (
                "Press a keyboard key or shortcut. "
                "Examples: 'ctrl+t' (new tab), 'ctrl+c' (copy), 'ctrl+v' (paste), "
                "'alt+Tab' (switch window), 'Return' (enter), 'Escape', 'ctrl+l' (address bar), "
                "'ctrl+shift+n' (incognito), 'F5' (refresh), 'super' (launcher), "
                "'ctrl+Tab' (next tab), 'ctrl+shift+Tab' (prev tab)"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {"type": "string", "description": "Key or combo, e.g. 'ctrl+t'"}
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": (
                "Open an application. Supported names: "
                "whatsapp, telegram, vscode, terminal, files, browser, chrome, firefox, "
                "email, gmail, supabase, github, slack, spotify, discord, notion, youtube, "
                "calculator, settings, system monitor, htop, jupyter, pycharm. "
                "Or any app by its binary name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "App name or binary"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a URL in the browser. Adds https:// automatically if missing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": "Navigate the currently focused browser to a URL (uses Ctrl+L shortcut). Falls back to open_url if browser not focused.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "new_browser_tab",
            "description": "Open a new browser tab, optionally navigating to a URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open (optional)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "focus_window",
            "description": "Bring a window to focus by searching its title. Use list_windows first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Window title substring to match"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_windows",
            "description": "List all open windows on the desktop with their IDs and titles.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll_at",
            "description": "Scroll up or down on the current page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down"]},
                    "amount": {"type": "integer", "description": "Scroll steps (default 3)"}
                },
                "required": ["direction"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file from Bas's filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path (supports ~/...)"},
                    "max_chars": {"type": "integer", "description": "Max chars to return (default 8000)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file on Bas's filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: ~)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_folder_gui",
            "description": "Open a folder in the graphical file manager (Nautilus).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Get current clipboard content.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Copy text to the clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "install_packages",
            "description": "Install Python packages via pip. Returns install output. Bot can be restarted after to load new packages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "packages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of pip package names"
                    }
                },
                "required": ["packages"]
            }
        }
    },
    # ── Web browsing tools (Playwright) ──────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "web_browse",
            "description": (
                "Browse a URL with full JavaScript rendering (headless Chromium). "
                "Returns page title, text content, links, and a screenshot. "
                "Handles cookie popups automatically. "
                "Use this for JS-heavy sites, SPAs, or when curl/scraping fails."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to browse"},
                    "extract_selector": {
                        "type": "string",
                        "description": "CSS selector to extract text from (default: body)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web via DuckDuckGo. Returns a list of results with "
                "titles, URLs, and snippets. Use this to find information online."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_research",
            "description": (
                "Deep multi-page research on a topic. Searches the web, visits "
                "multiple pages, extracts content, and compiles findings. "
                "Use for thorough research requiring multiple sources."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Research topic or question"},
                    "max_pages": {
                        "type": "integer",
                        "description": "Max pages to visit (default: 10)"
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fill_form",
            "description": (
                "Navigate to a URL and fill form fields. "
                "Fields are matched by name, id, or placeholder text."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL with the form"},
                    "fields": {
                        "type": "object",
                        "description": "Mapping of field name/label → value to fill"
                    },
                    "submit": {
                        "type": "boolean",
                        "description": "Whether to click submit after filling (default: false)"
                    }
                },
                "required": ["url", "fields"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_get_links",
            "description": "Get all links from a webpage, optionally filtered by a regex pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to get links from"},
                    "filter_pattern": {
                        "type": "string",
                        "description": "Regex pattern to filter URLs/text (optional)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_click",
            "description": (
                "Browse to a URL and click an element by its visible text. "
                "Returns the page state after clicking."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to navigate to"},
                    "click_text": {
                        "type": "string",
                        "description": "Visible text of element to click"
                    }
                },
                "required": ["url", "click_text"]
            }
        }
    },
    # ── Document processing tools ────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "read_pdf",
            "description": "Extract text from a PDF file. Can specify page range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to PDF file"},
                    "pages": {"type": "string", "description": "Page range: 'all', '1-5', '3', '1,3,5' (default: all)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pdf_extract_tables",
            "description": "Extract tables from a PDF and return them as markdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to PDF file"},
                    "pages": {"type": "string", "description": "Page range (default: all)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_excel",
            "description": "Read an Excel (.xlsx) file and return contents as a markdown table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to Excel file"},
                    "sheet": {"type": "string", "description": "Sheet name (default: active sheet)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_excel",
            "description": "Create or overwrite an Excel file with data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Output path for Excel file"},
                    "data": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "string"}},
                        "description": "List of rows, each row is a list of cell values"
                    },
                    "sheet_name": {"type": "string", "description": "Sheet name (default: Sheet1)"}
                },
                "required": ["path", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "excel_update_cell",
            "description": "Update a specific cell in an existing Excel file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to Excel file"},
                    "sheet": {"type": "string", "description": "Sheet name"},
                    "cell": {"type": "string", "description": "Cell reference, e.g. 'B5', 'A1'"},
                    "value": {"type": "string", "description": "New value for the cell"}
                },
                "required": ["path", "sheet", "cell", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ocr_image",
            "description": "Extract text from an image using OCR (Tesseract). Works on screenshots, photos of documents, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to image file"},
                    "lang": {"type": "string", "description": "Language: 'eng', 'ind', 'eng+ind' (default: eng)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ocr_pdf",
            "description": "OCR a scanned PDF (image-based). Extracts text from page images using Tesseract.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to scanned PDF"},
                    "lang": {"type": "string", "description": "Language (default: eng)"},
                    "pages": {"type": "string", "description": "Page range (default: all)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_docx",
            "description": "Read a Microsoft Word (.docx) document and return its text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to .docx file"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "organize_files",
            "description": "Organize files in a directory by grouping them into subfolders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to organize"},
                    "strategy": {
                        "type": "string",
                        "enum": ["by_type", "by_date"],
                        "description": "Organization strategy (default: by_type)"
                    }
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "Find files matching a glob pattern in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to search"},
                    "pattern": {"type": "string", "description": "Glob pattern, e.g. '*.pdf', '**/*.py'"}
                },
                "required": ["directory", "pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_info",
            "description": "Get detailed information about a file (size, type, dates, permissions).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"}
                },
                "required": ["path"]
            }
        }
    },
    # ── Email tools ──────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "email_check_inbox",
            "description": "Check email inbox. Lists recent or unread emails with sender, subject, and UID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max emails to show (default: 10)"},
                    "unread_only": {"type": "boolean", "description": "Only show unread (default: true)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "email_read",
            "description": "Read a specific email by its UID. Returns full sender, subject, body, and attachments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "uid": {"type": "string", "description": "Email UID (from email_check_inbox)"}
                },
                "required": ["uid"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "email_send",
            "description": "Send an email. Specify recipient, subject, and body.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body text"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "email_reply",
            "description": "Reply to an email by its UID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "uid": {"type": "string", "description": "UID of email to reply to"},
                    "body": {"type": "string", "description": "Reply body text"}
                },
                "required": ["uid", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "email_search",
            "description": "Search emails by subject text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search text"},
                    "limit": {"type": "integer", "description": "Max results (default: 20)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "email_summarize",
            "description": "Get a summary of the email inbox (recent emails for overview).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max emails to include (default: 20)"}
                }
            }
        }
    },
    # ── Git tools ────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Show git status (working tree, staged changes).",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Repository path (default: ~/swarm-bot)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Show git diff of changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Repository path"},
                    "staged": {"type": "boolean", "description": "Show staged changes only (default: false)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_log",
            "description": "Show recent git commit history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "n": {"type": "integer", "description": "Number of commits to show (default: 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Stage and commit changes with a message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "message": {"type": "string", "description": "Commit message"},
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific files to stage (default: all)"
                    }
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_branch",
            "description": "List, create, or checkout a git branch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "name": {"type": "string", "description": "Branch name (empty = list all)"},
                    "checkout": {"type": "boolean", "description": "Checkout the branch (default: false)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_pull",
            "description": "Pull latest changes from remote.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_push",
            "description": "Push commits to remote.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_stash",
            "description": "Git stash operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "action": {"type": "string", "enum": ["save", "pop", "list", "drop"], "description": "Stash action (default: save)"}
                }
            }
        }
    },
    # ── Dev tools ────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run tests (pytest, unittest) and return results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to test directory or file"},
                    "framework": {"type": "string", "enum": ["pytest", "unittest"], "description": "Test framework (default: pytest)"},
                    "args": {"type": "string", "description": "Additional arguments"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lint_code",
            "description": "Lint code for errors and style issues.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File or directory to lint"},
                    "tool": {"type": "string", "enum": ["ruff", "flake8", "pylint"], "description": "Linter (default: ruff)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_in_codebase",
            "description": "Search for a text pattern across code files (grep-like).",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern (regex)"},
                    "path": {"type": "string", "description": "Root directory (default: .)"},
                    "file_type": {"type": "string", "description": "File glob pattern (default: *.py)"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_codebase",
            "description": "Quick codebase analysis: file count, line counts, structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Root directory (default: .)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "db_query",
            "description": "Execute a SQL query against a database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"},
                    "db_path": {"type": "string", "description": "Database file path (for SQLite)"},
                    "db_type": {"type": "string", "enum": ["sqlite", "postgres", "mysql"], "description": "Database type (default: sqlite)"}
                },
                "required": ["query"]
            }
        }
    },
    # ── System Maintenance ──────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "check_disk_space",
            "description": "Check disk usage on all partitions. Alerts if any partition exceeds threshold.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {"type": "integer", "description": "Alert threshold percentage (default: 80)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_memory_usage",
            "description": "Check RAM and swap memory usage.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_gpu_health",
            "description": "Check GPU status, temperature, memory usage, and utilization via nvidia-smi.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_services",
            "description": "Check systemd service status for specified services.",
            "parameters": {
                "type": "object",
                "properties": {
                    "services": {"type": "string", "description": "Comma-separated service names (default: swarm-bot,ollama)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "system_cleanup",
            "description": "Clean temp files, old logs, pip cache, apt cache. Use dry_run=true to preview.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dry_run": {"type": "boolean", "description": "If true, show what would be cleaned without deleting (default: true)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_updates",
            "description": "Check for available system (apt) and Python (pip) package updates.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "driver_status",
            "description": "Check GPU driver version, CUDA status, PyTorch GPU support, and Ollama models.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "full_maintenance_check",
            "description": "Run all system health checks: disk, memory, GPU, services, drivers, updates.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────

async def execute_tool(name: str, args: dict[str, Any]) -> Any:
    """Dispatch a tool call. Returns string result or screenshot path."""
    from computer_agent import display as _display_mod
    from computer_agent import shell as _shell_mod

    dispatch = {
        "shell_execute": lambda a: _shell_mod.run_shell(a.get("command", "echo ''"), a.get("timeout", 30)),
        "take_screenshot": lambda a: _display_mod.take_screenshot(),
        "mouse_click": lambda a: _display_mod.mouse_click(a["x"], a["y"], a.get("button", "left")),
        "keyboard_type": lambda a: _display_mod.keyboard_type(a["text"], a.get("delay_ms", 30)),
        "key_press": lambda a: _display_mod.key_press(a["keys"]),
        "open_app": lambda a: _shell_mod.open_app(a["app_name"]),
        "open_url": lambda a: _shell_mod.open_url(a["url"]),
        "browser_navigate": lambda a: _display_mod.browser_navigate(a["url"]),
        "new_browser_tab": lambda a: _display_mod.new_browser_tab(a.get("url", "")),
        "focus_window": lambda a: _display_mod.focus_window(a["pattern"]),
        "list_windows": lambda a: _display_mod.list_windows(),
        "scroll_at": lambda a: _display_mod.scroll_at(a.get("direction", "down"), a.get("amount", 3)),
        "read_file": lambda a: _display_mod.read_file(a["path"], a.get("max_chars", 8000)),
        "write_file": lambda a: _display_mod.write_file(a["path"], a["content"]),
        "list_directory": lambda a: _display_mod.list_directory(a.get("path", "~")),
        "open_folder_gui": lambda a: _display_mod.open_folder_gui(a.get("path", "~")),
        "get_clipboard": lambda a: _display_mod.get_clipboard(),
        "set_clipboard": lambda a: _display_mod.set_clipboard(a["text"]),
        "install_packages": lambda a: _shell_mod.install_packages(a["packages"]),
        "web_browse": lambda a: _web_browse(a),
        "web_search": lambda a: _web_search(a),
        "web_research": lambda a: _web_research(a),
        "web_fill_form": lambda a: _web_fill_form(a),
        "web_get_links": lambda a: _web_get_links(a),
        "web_click": lambda a: _web_click(a),
        "read_pdf": lambda a: _doc_call("read_pdf", a),
        "pdf_extract_tables": lambda a: _doc_call("pdf_extract_tables", a),
        "read_excel": lambda a: _doc_call("read_excel", a),
        "write_excel": lambda a: _doc_call("write_excel", a),
        "excel_update_cell": lambda a: _doc_call("excel_update_cell", a),
        "ocr_image": lambda a: _doc_call("ocr_image", a),
        "ocr_pdf": lambda a: _doc_call("ocr_pdf", a),
        "read_docx": lambda a: _doc_call("read_docx", a),
        "organize_files": lambda a: _doc_call("organize_files", a),
        "find_files": lambda a: _doc_call("find_files", a),
        "file_info": lambda a: _doc_call("file_info", a),
        "email_check_inbox": lambda a: _email_call("check_inbox", a),
        "email_read": lambda a: _email_call("read_email", a),
        "email_send": lambda a: _email_call("send_email", a),
        "email_reply": lambda a: _email_call("reply_email", a),
        "email_search": lambda a: _email_call("search_emails", a),
        "email_summarize": lambda a: _email_call("summarize_inbox", a),
        "git_status": lambda a: _git_call("git_status", a),
        "git_diff": lambda a: _git_call("git_diff", a),
        "git_log": lambda a: _git_call("git_log", a),
        "git_commit": lambda a: _git_call("git_commit", a),
        "git_branch": lambda a: _git_call("git_branch", a),
        "git_pull": lambda a: _git_call("git_pull", a),
        "git_push": lambda a: _git_call("git_push", a),
        "git_stash": lambda a: _git_call("git_stash", a),
        "run_tests": lambda a: _dev_call("run_tests", a),
        "lint_code": lambda a: _dev_call("lint_code", a),
        "find_in_codebase": lambda a: _dev_call("find_in_codebase", a),
        "analyze_codebase": lambda a: _dev_call("analyze_codebase", a),
        "db_query": lambda a: _dev_call("db_query", a),
        "check_disk_space": lambda a: _maint_call("check_disk_space", a),
        "check_memory_usage": lambda a: _maint_call("check_memory_usage", a),
        "check_gpu_health": lambda a: _maint_call("check_gpu_health", a),
        "check_services": lambda a: _maint_call("check_services", a),
        "system_cleanup": lambda a: _maint_call("system_cleanup", a),
        "check_updates": lambda a: _maint_call("check_updates", a),
        "driver_status": lambda a: _maint_call("driver_status", a),
        "full_maintenance_check": lambda a: _maint_call("full_maintenance_check", a),
    }

    if name not in dispatch:
        return f"unknown tool: {name}"

    try:
        result = await dispatch[name](args)
        return result
    except KeyError as e:
        return f"missing required arg: {e}"
    except Exception as e:
        return f"tool error ({name}): {e}"



