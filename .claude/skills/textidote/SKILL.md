---
name: textidote
description: "LaTeX spelling, grammar and style linter powered by Textidote + LanguageTool. Use to check a .tex file for: spelling errors, grammar issues, missing spaces before citations, incorrect capitalization in titles, broken figure references, caption punctuation, over-long lines, and dozens of style rules. Complements /paperdebugger (structural review) and /genai-proofreader (persona critique) with automated rule-based linting."
trigger: /textidote
---

# /textidote

Lint LaTeX files for spelling, grammar, style, and structural issues using Textidote — a LaTeX-aware linter that maps LanguageTool warnings back to original source positions.

**Upstream:** https://github.com/sylvainhalle/textidote (GPL-3.0, 1048 stars, by Sylvain Hallé)

## MCP Tools

All tools available via the `textidote-mcp` MCP server (`tools/mcpServers/textidote_mcp/server.py`):

| Tool | What it does |
|------|-------------|
| `lint_latex` | Full LaTeX lint: grammar + spelling (via LanguageTool) + LaTeX-specific rules (capitalization, spacing, references, captions, etc). Returns structured warnings with location, message, rule ID, and excerpt. |
| `check_grammar` | Check a plain text snippet for spelling and grammar without LaTeX parsing. |
| `clean_latex` | Strip all LaTeX markup from a .tex file and return plain text with word/character count. |

## Quick Usage

```
/textidote lint: papers/my-paper/main.tex
/textidote lint: papers/my-paper/main.tex — language: en_UK
/textidote lint: papers/my-paper/main.tex — language: en, ignore_rules: sh:001,sh:002
/textidote grammar: "check this sentence for errors"
/textidote clean: papers/my-paper/main.tex
```

## Direct CLI Usage (without MCP)

```bash
# Full lint with grammar check
java -jar tools/textidote/textidote.jar --check en --output singleline paper.tex

# LaTeX-only rules (skip grammar)
java -jar tools/textidote/textidote.jar --output singleline paper.tex

# HTML report (view in browser)
java -jar tools/textidote/textidote.jar --output html paper.tex > report.html

# Clean markup to plain text
java -jar tools/textidote/textidote.jar --clean paper.tex > clean.txt

# Ignore specific rules
java -jar tools/textidote/textidote.jar --ignore sh:001,sh:c:001 paper.tex
```

## Rule Categories

Textidote checks hundreds of rules. Key categories:

| Category | Rule prefix | Examples |
|----------|-----------|---------|
| **Capitalization** | `sh:0xx` | Section titles should start with capital letter; not be all caps |
| **Punctuation** | `sh:c:0xx` | Space before/after citations; caption ending with period |
| **Structure** | `sh:1xx` | Consecutive sections; very short sections; figure labels/references |
| **Spacing** | `sh:s:0xx` | Double spaces; spaces before punctuation |
| **Spelling/Grammar** | `LT:xxxx` | LanguageTool rules for spelling, grammar, style |
| **Formatting** | `sh:f:0xx` | Absolute figure paths; manual line breaks; \\\\ usage |
| **References** | `sh:r:0xx` | Unreferenced figures; malformed citations |

## How Textidote Works

1. Reads the .tex file and strips LaTeX markup (commands, environments, math mode)
2. Passes the clean text to LanguageTool for grammar/spell checking
3. Maps LanguageTool position messages back to original .tex line:column positions
4. Applies LaTeX-specific rules (capitalization checks, citation spacing, figure references)
5. Reports warnings in single-line, plain, HTML, or JSON format

## Integration

- **/paperdebugger** — structural/checklist review. Run first for a quick quality gate.
- **/textidote** — automated rule-based linting. Run second for spelling, grammar, and style.
- **/genai-proofreader** — persona-based full-text review. Run third for deep critique.
- **/paperops** — LaTeX compilation. Run textidote before final build to catch issues.

## Wrapper Script

```
tools/textidote/textidote.sh <textidote args>
```

The JAR (215 MB) is at `tools/textidote/textidote.jar`. Requires Java 8+.
