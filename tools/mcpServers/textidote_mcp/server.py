"""Textidote MCP Server — LaTeX spelling, grammar and style checking.

Wraps Textidote (https://github.com/sylvainhalle/textidote) as MCP tools.
Textidote is a LaTeX-aware linter that reads .tex files, removes markup,
passes clean text to LanguageTool for grammar/spell checking, and maps
warnings back to original line/column positions.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

JAR_PATH = os.path.expanduser("~/swarm-bot/tools/textidote/textidote.jar")


def mcp_log(msg: str) -> None:
    print(json.dumps({"jsonrpc": "2.0", "method": "log", "params": {"message": msg}}), file=sys.stderr, flush=True)


def respond(id: int | None, result: Any = None, error: dict | None = None) -> None:
    body: dict[str, Any] = {"jsonrpc": "2.0"}
    if id is not None:
        body["id"] = id
    if error:
        body["error"] = error
    else:
        body["result"] = result
    print(json.dumps(body), flush=True)


TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "lint_latex",
        "description": "Lint a LaTeX file for spelling, grammar, style, and structural issues. Uses Textidote + LanguageTool. Returns structured warnings with file, line, column, severity, rule ID, and message. Supports multiple output formats.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tex_path": {
                    "type": "string",
                    "description": "Path to the .tex file to lint."
                },
                "language": {
                    "type": "string",
                    "enum": ["en", "en_UK", "en_CA", "fr", "de", "es", "pt", "nl", "pl"],
                    "description": "Language code for grammar/spell checking (default: en)."
                },
                "first_lang": {
                    "type": "string",
                    "description": "First language for false-friend detection (e.g. 'de' for German speakers writing English)."
                },
                "ignore_rules": {
                    "type": "string",
                    "description": "Comma-separated list of rule IDs to ignore (e.g. 'sh:001,sh:002')."
                },
                "ignore_latex_errors": {
                    "type": "boolean",
                    "description": "If true, skip grammar/spell check and only report LaTeX-specific rules (capitalization, spacing, references, etc).",
                    "default": False
                }
            },
            "required": ["tex_path"]
        }
    },
    {
        "name": "check_grammar",
        "description": "Check a plain text snippet for spelling and grammar errors using LanguageTool. Textidote is not needed for this — directly uses LanguageTool rules.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Plain text to check."
                },
                "language": {
                    "type": "string",
                    "enum": ["en", "en_UK", "fr", "de", "es", "pt"],
                    "description": "Language code (default: en)."
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "clean_latex",
        "description": "Strip LaTeX markup from a .tex file, returning only the plain text content. Useful for feeding into other tools or for word count.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tex_path": {
                    "type": "string",
                    "description": "Path to the .tex file to clean."
                }
            },
            "required": ["tex_path"]
        }
    },
]


def _run_textidote(args: list[str], cwd: str | None = None) -> tuple[str, str, int]:
    cmd = ["java", "-jar", JAR_PATH] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or os.getcwd(), timeout=120)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        raise RuntimeError("Textidote timed out after 120s")
    except FileNotFoundError:
        raise RuntimeError("Java not found. Install Java 8+ to use Textidote.")


def _parse_singleline(output: str) -> list[dict]:
    """Parse Textidote single-line output into structured warnings."""
    warnings = []
    # Pattern: file(LxxCyy-LxxCyy): message "excerpt"
    pat = re.compile(r'^(.+)\((\?|L\d+C\d+-L\d+C\d+)\):\s*(.+?)\s+"(.+)"\s*$', re.MULTILINE)
    for m in pat.finditer(output):
        location = m.group(2)
        message = m.group(3).strip()
        excerpt = m.group(4).strip()[:200]
        # Try to extract rule ID from message
        rule_id = ""
        rid_m = re.search(r'\[([\w:]+)\]$', message)
        if rid_m:
            rule_id = rid_m.group(1)
            message = re.sub(r'\s*\[[\w:]+\]$', '', message)
        warnings.append({
            "location": location,
            "message": message,
            "excerpt": excerpt,
            "rule_id": rule_id,
        })
    return warnings


def _execute_tool(name: str, args: dict) -> Any:
    if name == "lint_latex":
        tex_path = os.path.abspath(args["tex_path"])
        if not os.path.isfile(tex_path):
            return {"error": f"File not found: {tex_path}"}
        lang = args.get("language", "en")
        cmd_opts = ["--output", "singleline", "--no-color"]
        if args.get("ignore_latex_errors"):
            cmd_opts.extend(["--check", "none"])
        else:
            cmd_opts.extend(["--check", lang])
        if args.get("first_lang"):
            cmd_opts.extend(["--firstlang", args["first_lang"]])
        if args.get("ignore_rules"):
            cmd_opts.extend(["--ignore", args["ignore_rules"]])
        cmd_opts.append(tex_path)
        stdout, stderr, rc = _run_textidote(cmd_opts)
        # Count total warnings from stderr
        warning_count = 0
        wc_m = re.search(r'Found (\d+) warning', stderr)
        if wc_m:
            warning_count = int(wc_m.group(1))
        warnings = _parse_singleline(stdout)
        return {
            "file": tex_path,
            "language": lang,
            "total_warnings": warning_count,
            "parsed_warnings": len(warnings),
            "warnings": warnings[:100],
            "return_code": rc,
            "summary": f"Found {warning_count} warning(s). Parsed {len(warnings)} structured warnings."
        }
    elif name == "check_grammar":
        text = args["text"]
        with open("/tmp/textidote_grammar_check.txt", "w") as f:
            f.write(text)
        lang = args.get("language", "en")
        cmd_opts = ["--output", "singleline", "--no-color", "--check", lang, "--read-all", "/tmp/textidote_grammar_check.txt"]
        stdout, stderr, rc = _run_textidote(cmd_opts)
        warnings = _parse_singleline(stdout)
        return {"language": lang, "total": len(warnings), "warnings": warnings[:50]}
    elif name == "clean_latex":
        tex_path = os.path.abspath(args["tex_path"])
        if not os.path.isfile(tex_path):
            return {"error": f"File not found: {tex_path}"}
        stdout, stderr, rc = _run_textidote(["--clean", "--no-color", tex_path])
        # Remove ANSI codes
        clean = re.sub(r'\x1b\[[0-9;]*m', '', stdout)
        word_count = len(clean.split())
        char_count = len(clean)
        return {
            "file": tex_path,
            "word_count": word_count,
            "character_count": char_count,
            "content": clean,
        }
    raise ValueError(f"Unknown tool: {name}")


def handle_request(msg: dict) -> None:
    msg_id = msg.get("id")
    method = msg.get("method", "")
    params = msg.get("params", {})
    if method == "initialize":
        respond(msg_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "textidote-mcp", "version": "1.0.0"}
        })
    elif method == "notifications/initialized":
        respond(None, {})
    elif method == "tools/list":
        respond(msg_id, {"tools": TOOL_DEFS})
    elif method == "tools/call":
        tool_name = params.get("name", "")
        t_args = params.get("arguments", {})
        try:
            result = _execute_tool(tool_name, t_args)
            respond(msg_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
        except Exception as e:
            respond(msg_id, error={"code": -32000, "message": f"{type(e).__name__}: {e}"})
    else:
        respond(msg_id, error={"code": -32601, "message": f"Method not found: {method}"})


def main():
    mcp_log("Textidote MCP server starting...")
    if not os.path.isfile(JAR_PATH):
        mcp_log(f"ERROR: textidote.jar not found at {JAR_PATH}")
    buf = ""
    for line in sys.stdin:
        buf += line
        try:
            msg = json.loads(buf)
            buf = ""
            handle_request(msg)
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    main()
