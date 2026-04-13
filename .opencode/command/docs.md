---
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [target] [--watch] | module-name | api | architecture
description: Generate or update documentation for a module, API, or architecture. Follows wiki SCHEMA.md format.
---

# /docs — Documentation Generation

## STEP 1 — Determine Scope

If target = module-name:
```bash
ls core/[module-name]/
ls handlers/[module-name]/
```

If target = api:
```bash
grep -rn "async def\|def " --include="*.py" handlers/ | grep -v "__\|test\|#" | head -30
```

If target = architecture:
```bash
cat wiki/SCHEMA.md | head -50
cat wiki/architecture/legion-module-map.md 2>/dev/null | head -30
```

## STEP 2 — Generate Documentation

For modules, create a wiki article at `wiki/[category]/[module-name].md`:

Required frontmatter (from wiki/SCHEMA.md):
```yaml
---
title: [Module Name]
created: 2026-04-13
tags: [legion, python, module]
summary: [2-3 sentence description]
wikilinks:
  - [[concepts/legion-architecture]]
  - [[core/agent-registry]]
---

## Overview
[What this module does]

## Key Functions
[Function list with purpose]

## Usage Example
[Real code example with actual paths]

## Current Status
[Active | Stable | Experimental]
```

## STEP 3 — Verify

```bash
# Check frontmatter validity
python -c "import yaml; yaml.safe_load(open('wiki/[category]/[module-name].md').read().split('---')[1])"

# Check wikilinks resolve
python3 << 'EOF'
import glob, re
f = 'wiki/[category]/[module-name].md'
links = re.findall(r'\[\[([^\]]+)\]\]', open(f).read())
print(f"Links found: {len(links)}")
EOF
```

## STEP 4 — Update SCHEMA.md if needed

If new category: add to wiki/SCHEMA.md category list
