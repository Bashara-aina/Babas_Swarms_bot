# Textidote — LaTeX Spelling, Grammar & Style Checker

## Overview

TeXtidote is a LaTeX-aware linter that checks .tex files for spelling, grammar, style, and structural issues. It removes LaTeX markup, passes the clean text to LanguageTool for linguistic analysis, and maps all warnings back to original source positions.

**Upstream:** https://github.com/sylvainhalle/textidote  
**License:** GPL-3.0 (by Sylvain Hallé, Université du Québec à Chicoutimi)  
**Language:** Java (runs on JAR, requires Java 8+)  
**Latest release:** v0.9 (2023-03-08)

## Installation in this project

**JAR:** `tools/textidote/textidote.jar` (215 MB)  
**Wrapper:** `tools/textidote/textidote.sh`  
**MCP Server:** `tools/mcpServers/textidote_mcp/server.py`  
**Skill:** `/textidote`

## Usage

### Basic lint
```bash
java -jar tools/textidote/textidote.jar --check en paper.tex
```

### Output formats
- `--output html` — HTML report viewable in browser
- `--output plain` (default) — Console output with colors
- `--output singleline` — Parseable one-line-per-warning format
- `--output json` — JSON output (machine-readable)

### Language support
```bash
--check en        # English (US)
--check en_UK     # English (British)
--check fr        # French
--check de        # German
--firstlang de    # False-friend detection for German speakers writing English
```

### Dictionary
```bash
--dict dico.txt   # Custom word list (one per line)
```
Auto-loads `.aspell.XX.pws` (Aspell local dictionary) if present.

### Ignoring rules
```bash
--ignore sh:001,sh:002,sh:c:001
```

### Ignoring environments
```bash
--remove itemize     # Skip content inside itemize environments
```

### Removing macros
```bash
--remove-macros foo  # Remove all occurrences of \foo
```

### Read all (for sub-files)
```bash
--read-all           # Process file even without \begin{document}
```

## Output Format (single-line)

```
file.tex(L25C1-L25C25): A section title should start with a capital letter. "\section{a first section}"
```

Each line: `file(LxxCyy-LxxCyy): message "excerpt"` where `L` = line, `C` = column.

## Rule Reference

### sh:0xx — Capitalization
- `sh:001` — Section title should start with a capital letter
- `sh:002` — Section title should not end with punctuation
- `sh:003` — Section title should not be written in all caps

### sh:c:0xx — Citations and references
- `sh:c:001` — Add space before citation
- `sh:c:002` — Remove space between citation and punctuation
- `sh:c:003` — Space before reference

### sh:1xx — Section structure
- `sh:101` — Consecutive sections
- `sh:102` — Section very short
- `sh:103` — Figure should be referenced in text

### sh:s:0xx — Spacing
- `sh:s:001` — Double space
- `sh:s:002` — Space before punctuation
- `sh:s:003` — Space after comma

### sh:f:0xx — Formatting
- `sh:f:001` — Absolute path for figure
- `sh:f:002` — Caption should end with period
- `sh:f:003` — Line break in paragraph
- `sh:f:004` — Use of \\\\

### sh:r:0xx — Labels and references
- `sh:r:001` — Unreferenced label

## Comparison with Other Paper Tools

| Aspect | textidote | paperdebugger | genai-proofreader |
|--------|-----------|--------------|-------------------|
| Check type | Rule-based linting | Structural checklists | LLM persona review |
| Grammar/spelling | Yes (LanguageTool) | No | Via LLM |
| LaTeX-aware | Yes (native .tex parser) | Regex-based | Full parser |
| Speed | Fast (<1s) | Fast | Slow (API calls) |
| Output | Line/column warnings | Severity-tagged issues | Full-text critique |
| False positives | Can be silenced | Precise | Subjective |
| Requires Java | Yes (8+) | No | No |

Run textidote as the **first automated pass** before human or LLM review.
